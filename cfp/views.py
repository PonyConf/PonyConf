from math import ceil
from django.core.mail import send_mail
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, TemplateView
from django.contrib import messages
from django.db.models import Q
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from django_select2.views import AutoResponseView

from functools import reduce

from mailing.models import Message
from mailing.forms import MessageForm
from .planning import Program
from .decorators import staff_required
from .mixins import StaffRequiredMixin, OnSiteMixin, OnSiteFormMixin
from .utils import is_staff
from .models import Participant, Talk, TalkCategory, Vote, Track, Tag, Room, Volunteer, Activity
from .forms import TalkForm, TalkStaffForm, TalkFilterForm, TalkActionForm, \
                   ParticipantForm, ParticipantStaffForm, ParticipantFilterForm, \
                   ConferenceForm, CreateUserForm, TrackForm, RoomForm, VolunteerForm, \
                   ACCEPTATION_VALUES, CONFIRMATION_VALUES


def home(request):
    if request.conference.home:
        return render(request, 'cfp/home.html')
    else:
        return redirect(reverse('talk-proposal'))


def volunteer_enrole(request):
    if not request.conference.volunteers_enrollment_is_open():
        raise PermissionDenied
    form = VolunteerForm(request.POST or None, conference=request.conference)
    if request.method == 'POST' and form.is_valid():
        volunteer = form.save(commit=False)
        volunteer.language = request.LANGUAGE_CODE
        volunteer.save()
        messages.success(request, _('Thank you for your participation! You can now subscribe to some activities.'))
        return redirect(reverse('volunteer', kwargs=dict(volunteer_id=volunteer.token)))
    return render(request, 'cfp/volunteer_enrole.html', {
        'activities': Activity.objects.filter(site=request.conference.site),
        'form': form,
    })


def volunteer(request, volunteer_id):
    volunteer = get_object_or_404(Volunteer, token=volunteer_id, site=request.conference.site)
    return render(request, 'cfp/volunteer.html', {
        'activities': Activity.objects.filter(site=request.conference.site),
        'volunteer': volunteer,
    })


def volunteer_activity(request, volunteer_id, activity, join):
    if not request.conference.volunteers_enrollment_is_open():
        raise PermissionDenied
    volunteer = get_object_or_404(Volunteer, token=volunteer_id, site=request.conference.site)
    activity = get_object_or_404(Activity, slug=activity, site=request.conference.site)
    if join:
        activity.volunteers.add(volunteer)
        activity.save()
        messages.success(request, _('Thank you for your participation!'))
    else:
        activity.volunteers.remove(volunteer)
        activity.save()
        messages.success(request, _('Okay, no problem!'))
    return redirect(reverse('volunteer', kwargs=dict(volunteer_id=volunteer.token)))


def talk_proposal(request, talk_id=None, participant_id=None):

    conference = request.conference
    site = conference.site
    if is_staff(request, request.user):
        categories = TalkCategory.objects.filter(site=site)
    else:
        categories = conference.opened_categories
    talk = None
    participant = None

    if talk_id and participant_id:
        talk = get_object_or_404(Talk, token=talk_id, site=site)
        participant = get_object_or_404(Participant, token=participant_id, site=site)
    elif not categories.exists():
        return render(request, 'cfp/closed.html')

    participant_form = ParticipantForm(request.POST or None, instance=participant)
    talk_form = TalkForm(request.POST or None, categories=categories, instance=talk)

    if request.method == 'POST' and talk_form.is_valid() and participant_form.is_valid():
        talk = talk_form.save(commit=False)
        talk.site = site

        participant, created = Participant.objects.get_or_create(email=participant_form.cleaned_data['email'], site=site)
        participant_form = ParticipantForm(request.POST, instance=participant)
        participant = participant_form.save()
        participant.language = request.LANGUAGE_CODE
        participant.save()

        talk.save()
        talk.speakers.add(participant)

        protocol = 'https' if request.is_secure() else 'http'
        base_url = protocol+'://'+site.domain
        url_talk_proposal_edit = base_url + reverse('talk-proposal-edit', args=[talk.token, participant.token])
        url_talk_proposal_speaker_add = base_url + reverse('talk-proposal-speaker-add', args=[talk.token])
        url_talk_proposal_speaker_edit = base_url + reverse('talk-proposal-speaker-edit', args=[talk.token, participant.token])
        body = _("""Hi {},

Your talk has been submitted for {}.

Here are the details of your talk:
Title: {}
Description: {}

You can at anytime:
- edit your talk: {}
- add a new co-speaker: {}
- edit your profile: {}

If you have any question, your can answer to this email.

Thanks!

{}

""").format(participant.name, conference.name, talk.title, talk.description, url_talk_proposal_edit, url_talk_proposal_speaker_add, url_talk_proposal_speaker_edit, conference.name)

        Message.objects.create(
            thread=participant.conversation,
            author=conference,
            from_email=conference.contact_email,
            content=body,
        )

        return render(request, 'cfp/complete.html', {'talk': talk, 'participant': participant})

    return render(request, 'cfp/propose.html', {
        'participant_form': participant_form,
        'site': site,
        'talk_form': talk_form,
    })


def talk_proposal_speaker_edit(request, talk_id, participant_id=None):

    talk = get_object_or_404(Talk, token=talk_id, site=request.conference.site)
    participant = None

    if participant_id:
        participant = get_object_or_404(Participant, token=participant_id, site=request.conference.site)

    participant_form = ParticipantForm(request.POST or None, instance=participant)

    if request.method == 'POST' and participant_form.is_valid():

        participant, created = Participant.objects.get_or_create(email=participant_form.cleaned_data['email'], site=request.conference.site)
        participant_form = ParticipantForm(request.POST, instance=participant)
        participant = participant_form.save()
        participant.save()

        talk.speakers.add(participant)

        return render(request,'cfp/complete.html', {'talk': talk, 'participant': participant})

    return render(request, 'cfp/speaker.html', {
        'participant_form': participant_form,
    })


def talk_acknowledgment(request, talk_id, confirm, participant_id=None):
    # TODO: handle multiple speakers case
    talk = get_object_or_404(Talk, token=talk_id, site=request.conference.site)
    if participant_id:
        participant = get_object_or_404(Participant, token=participant_id, site=request.conference.site)
    elif not is_staff(request, request.user):
        raise PermissionDenied
    else:
        participant = None
    if not talk.accepted:
        raise PermissionDenied
    if talk.confirmed != confirm:
        talk.confirmed = confirm
        talk.save()
        if confirm:
            confirmation_message= _('Your participation has been taken into account, thank you!')
            if participant:
                thread_note = _('Speaker %(speaker)s confirmed his/her participation.')
            else:
                thread_note = _('The talk have been confirmed.')
        else:
            confirmation_message = _('We have noted your unavailability.')
            if participant:
                thread_note = _('Speaker %(speaker)s CANCELLED his/her participation.')
            else:
                thread_note = _('The talk have been cancelled.')
        if participant_id:
            thread_note = thread_note % {'speaker': participant}
        Message.objects.create(thread=talk.conversation, author=participant or request.user, content=thread_note)
        messages.success(request, confirmation_message)
    else:
        if confirm:
            messages.warning(request, _('You already confirmed your participation to this talk.'))
        else:
            messages.warning(request, _('You already cancelled your participation to this talk.'))
    if participant:
        return redirect(reverse('talk-proposal-edit', kwargs=dict(talk_id=talk_id, participant_id=participant_id)))
    else:
        return redirect(reverse('talk-details', kwargs=dict(talk_id=talk_id)))


@staff_required
def staff(request):
    return render(request, 'cfp/staff/base.html')


@staff_required
def talk_list(request):
    talks = Talk.objects.filter(site=request.conference.site)
    # Filtering
    show_filters = False
    filter_form = TalkFilterForm(request.GET or None, site=request.conference.site)
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        if len(data['category']):
            show_filters = True
            talks = talks.filter(reduce(lambda x, y: x | y, [Q(category__pk=pk) for pk in data['category']]))
        if len(data['accepted']):
            show_filters = True
            talks = talks.filter(reduce(lambda x, y: x | y, [Q(accepted=dict(ACCEPTATION_VALUES)[status]) for status in data['accepted']]))
        if len(data['confirmed']):
            show_filters = True
            talks = talks.filter(accepted=True)
            talks = talks.filter(reduce(lambda x, y: x | y, [Q(confirmed=dict(CONFIRMATION_VALUES)[status]) for status in data['confirmed']]))
        if data['room'] != None:
            show_filters = True
            talks = talks.filter(room__isnull=not data['room'])
        if data['scheduled'] != None:
            show_filters = True
            talks = talks.filter(start_date__isnull=not data['scheduled'])
        if len(data['tag']):
            show_filters = True
            talks = talks.filter(tags__slug__in=data['tag'])
        if len(data['track']):
            show_filters = True
            q = Q()
            if 'none' in data['track']:
                data['track'].remove('none')
                q |= Q(track__isnull=True)
            if len(data['track']):
                q |= Q(track__slug__in=data['track'])
            talks = talks.filter(q)
        if data['vote'] != None:
            show_filters = True
            if data['vote']:
                talks = talks.filter(vote__user=request.user)
            else:
                talks = talks.exclude(vote__user=request.user)
        if data['materials'] != None:
            show_filters = True
            talks = talks.filter(materials__isnull=not data['materials'])
        if data['video'] != None:
            show_filters = True
            if data['video']:
                talks = talks.exclude(video__exact='')
            else:
                talks = talks.filter(video__exact='')
    # Action
    action_form = TalkActionForm(request.POST or None, talks=talks, site=request.conference.site)
    if request.method == 'POST' and action_form.is_valid():
        data = action_form.cleaned_data
        for talk in data['talks']:
            talk = Talk.objects.get(site=request.conference.site, token=talk)
            if data['decision'] != None and data['decision'] != talk.accepted:
                if data['decision']:
                    note = _("The talk has been accepted.")
                else:
                    note = _("The talk has been declined.")
                Message.objects.create(thread=talk.conversation, author=request.user, content=note)
                talk.accepted = data['decision']
            if data['track']:
                talk.track = Track.objects.get(site=request.conference.site, slug=data['track'])
            if data['tag']:
                talk.tags.add(Tag.objects.get(site=request.conference.site, slug=data['tag']))
            if data['room']:
                talk.room = Room.objects.get(site=request.conference.site, slug=data['room'])
            talk.save()
        return redirect(request.get_full_path())
    # Sorting
    if request.GET.get('order') == 'desc':
        sort_reverse = True
    else:
        sort_reverse = False
    SORT_MAPPING = {
        'title': 'title',
        'category': 'category',
        'status': 'accepted',
    }
    sort = request.GET.get('sort')
    if sort in SORT_MAPPING.keys():
        if sort_reverse:
            talks = talks.order_by('-' + SORT_MAPPING[sort])
        else:
            talks = talks.order_by(SORT_MAPPING[sort])
    # Sorting URLs
    sort_urls = dict()
    sort_glyphicons = dict()
    for c in SORT_MAPPING.keys():
        url = request.GET.copy()
        url['sort'] = c
        if c == sort:
            if sort_reverse:
                del url['order']
                glyphicon = 'sort-by-attributes-alt'
            else:
                url['order'] = 'desc'
                glyphicon = 'sort-by-attributes'
        else:
            glyphicon = 'sort'
        sort_urls[c] = url.urlencode()
        sort_glyphicons[c] = glyphicon
    talks = talks.prefetch_related('category', 'speakers', 'track', 'tags')
    return render(request, 'cfp/staff/talk_list.html', {
        'show_filters': show_filters,
        'talk_list': talks,
        'filter_form': filter_form,
        'action_form': action_form,
        'sort_urls': sort_urls,
        'sort_glyphicons': sort_glyphicons,
    })


@staff_required
def talk_details(request, talk_id):
    talk = get_object_or_404(Talk, token=talk_id, site=request.conference.site)
    message_form = MessageForm(request.POST or None)
    if request.method == 'POST' and message_form.is_valid():
        message = message_form.save(commit=False)
        message.author = request.user
        message.from_email = request.user.email
        message.thread = talk.conversation
        message.save()
        messages.success(request, _('Message sent!'))
        return redirect(reverse('talk-details', args=[talk.token]))
    return render(request, 'cfp/staff/talk_details.html', {
        'talk': talk,
    })


@staff_required
def talk_vote(request, talk_id, score):
    talk = get_object_or_404(Talk, token=talk_id, site=request.conference.site)
    vote, created = Vote.objects.get_or_create(talk=talk, user=request.user)
    vote.vote = int(score)
    vote.save()
    messages.success(request, _('Vote successfully created') if created else _('Vote successfully updated'))
    return redirect(talk.get_absolute_url())


@staff_required
def talk_decide(request, talk_id, accept):
    talk = get_object_or_404(Talk, token=talk_id, site=request.conference.site)
    if request.method == 'POST':
        talk.accepted = accept
        talk.save()
        # Does we need to send a notification to the proposer?
        m = request.POST.get('message', '').strip()
        if m:
            for participant in talk.speakers.all():
                Message.objects.create(thread=talk.conversation, author=request.user, content=m)
        # Save the decision in the talk's conversation
        if accept:
            note = _("The talk has been accepted.")
        else:
            note = _("The talk has been declined.")
        Message.objects.create(thread=talk.conversation, author=request.user, content=note)
        messages.success(request, _('Decision taken in account'))
        return redirect(talk.get_absolute_url())
    return render(request, 'cfp/staff/talk_decide.html', {
        'talk': talk,
        'accept': accept,
    })


@staff_required
def participant_list(request):
    participants = Participant.objects.filter(site=request.conference.site) \
                                      .extra(select={'lower_name': 'lower(name)'}) \
                                      .order_by('lower_name')
    # Filtering
    show_filters = False
    filter_form = ParticipantFilterForm(request.GET or None, site=request.conference.site)
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        talks = Talk.objects.filter(site=request.conference.site)
        if len(data['category']):
            show_filters = True
            talks = talks.filter(reduce(lambda x, y: x | y, [Q(category__pk=pk) for pk in data['category']]))
        if len(data['accepted']):
            show_filters = True
            talks = talks.filter(reduce(lambda x, y: x | y, [Q(accepted=dict(ACCEPTATION_VALUES)[status]) for status in data['accepted']]))
        if len(data['confirmed']):
            show_filters = True
            talks = talks.filter(accepted=True)
            talks = talks.filter(reduce(lambda x, y: x | y, [Q(confirmed=dict(CONFIRMATION_VALUES)[status]) for status in data['confirmed']]))
        if len(data['track']):
            show_filters = True
            q = Q()
            if 'none' in data['track']:
                data['track'].remove('none')
                q |= Q(track__isnull=True)
            if len(data['track']):
                q |= Q(track__slug__in=data['track'])
            talks = talks.filter(q)
        participants = participants.filter(talk__in=talks)
    contact_link = 'mailto:' + ','.join([participant.email for participant in participants.all()])
    return render(request, 'cfp/staff/participant_list.html', {
        'filter_form': filter_form,
        'participant_list': participants,
        'show_filters': show_filters,
        'contact_link': contact_link,
    })


@staff_required
def participant_details(request, participant_id):
    participant = get_object_or_404(Participant, token=participant_id, site=request.conference.site)
    message_form = MessageForm(request.POST or None)
    if request.method == 'POST' and message_form.is_valid():
        message = message_form.save(commit=False)
        message.author = request.user
        message.from_email = request.user.email
        message.thread = participant.conversation
        message.save()
        messages.success(request, _('Message sent!'))
        return redirect(reverse('participant-details', args=[participant.token]))
    return render(request, 'cfp/staff/participant_details.html', {
        'participant': participant,
    })


class ParticipantUpdate(StaffRequiredMixin, OnSiteMixin, UpdateView):
    model = Participant
    slug_field = 'token'
    slug_url_kwarg = 'participant_id'
    form_class = ParticipantStaffForm
    template_name = 'cfp/staff/participant_form.html'


@staff_required
def conference(request):
    form = ConferenceForm(request.POST or None, instance=request.conference)

    if request.method == 'POST' and form.is_valid():
        old_staff = set(request.conference.staff.all())
        new_conference = form.save()
        new_staff = set(new_conference.staff.all())
        added_staff = new_staff - old_staff
        protocol = 'https' if request.is_secure() else 'http'
        base_url = protocol+'://'+request.conference.site.domain
        url_login = base_url + reverse('login')
        url_password_reset = base_url + reverse('password_reset')
        msg_title = _('[{}] You have been added to the staff team').format(request.conference.name)
        msg_body_template = _("""Hi {},

You have been added to the staff team.

You can now:
- login: {}
- reset your password: {}

{}

""")
        # TODO: send bulk emails
        for user in added_staff:
            msg_body = msg_body_template.format(user.get_full_name(), url_login, url_password_reset, request.conference.name)
            send_mail(
                msg_title,
                msg_body,
                request.conference.from_email(),
                [user.email],
                fail_silently=False,
            )
        messages.success(request, _('Modifications successfully saved.'))
        return redirect(reverse('conference'))

    return render(request, 'cfp/staff/conference.html', {
        'form': form,
    })


class TalkUpdate(StaffRequiredMixin, OnSiteMixin, OnSiteFormMixin, UpdateView):
    model = Talk
    slug_field = 'token'
    slug_url_kwarg = 'talk_id'
    form_class = TalkStaffForm
    template_name = 'cfp/staff/talk_form.html'


class TrackMixin(OnSiteMixin):
    model = Track


class TrackList(StaffRequiredMixin, TrackMixin, ListView):
    template_name = 'cfp/staff/track_list.html'


class TrackFormMixin(OnSiteFormMixin, TrackMixin):
    template_name = 'cfp/staff/track_form.html'
    form_class = TrackForm
    success_url = reverse_lazy('track-list')


class TrackCreate(StaffRequiredMixin, TrackFormMixin, CreateView):
    pass


class TrackUpdate(StaffRequiredMixin, TrackFormMixin, UpdateView):
    pass


class RoomMixin(OnSiteMixin):
    model = Room


class RoomList(StaffRequiredMixin, RoomMixin, ListView):
    template_name = 'cfp/staff/room_list.html'


class RoomDetail(StaffRequiredMixin, RoomMixin, DetailView):
    template_name = 'cfp/staff/room_details.html'


class RoomFormMixin(RoomMixin):
    template_name = 'cfp/staff/room_form.html'
    form_class = RoomForm
    success_url = reverse_lazy('room-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'conference': self.request.conference,
        })
        return kwargs


class RoomCreate(StaffRequiredMixin, RoomFormMixin, CreateView):
    pass


class RoomUpdate(StaffRequiredMixin, RoomFormMixin, UpdateView):
    pass


@staff_required
def create_user(request):
    form = CreateUserForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _('User created successfully.'))
        return redirect(reverse('create-user'))

    return render(request, 'cfp/staff/create_user.html', {
        'form': form,
    })


def schedule(request, program_format, pending, cache, template):
    program = Program(site=request.conference.site, pending=pending, cache=cache)
    if program_format is None:
        return render(request, template, {'program': program.render('html')})
    elif program_format == 'html':
        return HttpResponse(program.render('html'))
    elif program_format == 'xml':
        return HttpResponse(program.render('xml'), content_type="application/xml")
    elif program_format == 'ics':
        response = HttpResponse(program.render('ics'), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename="planning.ics"'
        return response
    else:
        raise Http404(_("Format '%s' not available" % program_format))


def public_schedule(request, program_format):
    if not request.conference.schedule_available and not is_staff(request, request.user):
        raise PermissionDenied
    return schedule(request, program_format=program_format, pending=False, cache=True, template='cfp/schedule.html')


@staff_required
def staff_schedule(request, program_format):
    return schedule(request, program_format=program_format, pending=True, cache=False, template='cfp/staff/schedule.html')


class Select2View(StaffRequiredMixin, AutoResponseView):
    pass
