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
from django.core.mail import send_mail

from django_select2.views import AutoResponseView

from functools import reduce

from mailing.models import Message
from mailing.forms import MessageForm
from .planning import Program
from .decorators import speaker_required, staff_required
from .mixins import StaffRequiredMixin, OnSiteMixin, OnSiteFormMixin
from .utils import is_staff
from .models import Participant, Talk, TalkCategory, Vote, Track, Tag, Room, Volunteer, Activity
from .forms import TalkForm, TalkStaffForm, TalkFilterForm, TalkActionForm, \
                   ParticipantForm, ParticipantStaffForm, ParticipantFilterForm, \
                   ConferenceForm, CreateUserForm, TrackForm, RoomForm, \
                   VolunteerForm, VolunteerFilterForm, MailForm, \
                   ACCEPTATION_VALUES, CONFIRMATION_VALUES


def home(request):
    if request.conference.home:
        return render(request, 'cfp/home.html')
    else:
        return redirect(reverse('proposal-home'))


def volunteer_enrole(request):
    if not request.conference.volunteers_enrollment_is_open():
        raise PermissionDenied
    form = VolunteerForm(request.POST or None, conference=request.conference)
    if request.method == 'POST' and form.is_valid():
        volunteer = form.save(commit=False)
        volunteer.language = request.LANGUAGE_CODE
        volunteer.save()
        body = _("""Hi {},

Thank your for your help in the organization of the conference {}!

You can update your availability at anytime:

    {}

Thanks!

{}

""").format(volunteer.name, request.conference.name, volunteer.get_secret_url(full=True), request.conference.name)
        #Message.objects.create(
        #    thread=volunteer.conversation,
        #    author=request.conference,
        #    from_email=request.conference.contact_email,
        #    content=body,
        #)
        send_mail(
            subject=_('Thank you for your help!'),
            message=body,
            from_email='%s <%s>' % (request.conference.name, request.conference.contact_email),
            recipient_list=['%s <%s>' % (volunteer.name, volunteer.email)],
        )
        messages.success(request, _('Thank you for your participation! You can now subscribe to some activities.'))
        return redirect(reverse('volunteer-home', kwargs=dict(volunteer_id=volunteer.token)))
    return render(request, 'cfp/volunteer_enrole.html', {
        'activities': Activity.objects.filter(site=request.conference.site),
        'form': form,
    })


def volunteer_home(request, volunteer_id):
    volunteer = get_object_or_404(Volunteer, token=volunteer_id, site=request.conference.site)
    return render(request, 'cfp/volunteer.html', {
        'activities': Activity.objects.filter(site=request.conference.site),
        'volunteer': volunteer,
    })


def volunteer_update_activity(request, volunteer_id, activity, join):
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
    return redirect(reverse('volunteer-home', kwargs=dict(volunteer_id=volunteer.token)))


@staff_required
def volunteer_list(request):
    site = request.conference.site
    show_filters = False
    filter_form = VolunteerFilterForm(request.GET or None, site=site)
    # Filtering
    volunteers = Volunteer.objects.filter(site=site).order_by('pk').distinct().prefetch_related('activities')
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        if len(data['activity']):
            show_filters = True
            q = Q()
            if 'none' in data['activity']:
                data['activity'].remove('none')
                q |= Q(activities__isnull=True)
            if len(data['activity']):
                q |= Q(activities__slug__in=data['activity'])
            volunteers = volunteers.filter(q)
    contact_link = 'mailto:' + ','.join([volunteer.email for volunteer in volunteers.all()])
    return render(request, 'cfp/staff/volunteer_list.html', {
        'volunteer_list': volunteers,
        'filter_form': filter_form,
        'show_filters': show_filters,
        'contact_link': contact_link,
    })


@staff_required
def volunteer_details(request, volunteer_id):
    volunteer = get_object_or_404(Volunteer, site=request.conference.site, pk=volunteer_id)
    return render(request, 'cfp/staff/volunteer_details.html', {
        'volunteer': volunteer,
    })


def proposal_home(request):
    if is_staff(request, request.user):
        categories = TalkCategory.objects.filter(site=request.conference.site)
    else:
        categories = request.conference.opened_categories
    speaker_form = ParticipantForm(request.POST or None, conference=request.conference, social=False)
    talk_form = TalkForm(request.POST or None, categories=categories)
    if request.method == 'POST' and all(map(lambda f: f.is_valid(), [speaker_form, talk_form])):
        speaker = speaker_form.save(commit=False)
        speaker.site = request.conference.site
        speaker.save()
        talk = talk_form.save(commit=False)
        talk.site = request.conference.site
        talk.save()
        talk.speakers.add(speaker)
        base_url = ('https' if request.is_secure() else 'http') + '://' + request.conference.site.domain
        url_dashboard = base_url + reverse('proposal-dashboard', kwargs=dict(speaker_token=speaker.token))
        url_talk_details = base_url + reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk))
        url_speaker_add = base_url + reverse('proposal-speaker-add', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk))
        body = _("""Hi {},

Your talk has been submitted for {}.

Here are the details of your talk:
Title: {}
Description: {}

You can at anytime:
- review and edit your profile: {}
- review and edit your talk: {}
- add a new co-speaker: {}

If you have any question, your can answer to this email.

Thanks!

{}

""").format(
            speaker.name, request.conference.name,talk.title, talk.description,
            url_dashboard, url_talk_details, url_speaker_add,
            request.conference.name,
        )
        Message.objects.create(
            thread=speaker.conversation,
            author=request.conference,
            from_email=request.conference.contact_email,
            content=body,
        )
        messages.success(request, _('You proposition have been successfully submitted!'))
        return redirect(reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)))
    return render(request, 'cfp/proposal_home.html', {
        'speaker_form': speaker_form,
        'talk_form': talk_form,
    })


def proposal_mail_token(request):
    form = MailForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            speaker = Participant.objects.get(site=request.conference.site, email=form.cleaned_data['email'])
        except Participant.DoesNotExist:
            messages.error(request, _('Sorry, we do not know this email.'))
        else:

            base_url = ('https' if request.is_secure() else 'http') + '://' + request.conference.site.domain
            dashboard_url = base_url + reverse('proposal-dashboard', kwargs=dict(speaker_token=speaker.token))
            body = _("""Hi {},

Someone, probably you, ask to access your profile.
You can edit your talks or add new ones following this url:

  {}

If you have any question, your can answer to this email.

Sincerely,

{}

""").format(speaker.name, dashboard_url, request.conference.name)
            Message.objects.create(
                thread=speaker.conversation,
                author=request.conference,
                from_email=request.conference.contact_email,
                content=body,
            )
            messages.success(request, _('A email have been sent with a link to access to your profil.'))
            return redirect(reverse('proposal-mail-token'))
    return render(request, 'cfp/proposal_mail_token.html', {
        'form': form,
    })


@speaker_required
def proposal_dashboard(request, speaker):
    return render(request, 'cfp/proposal_dashboard.html', {
        'speaker': speaker,
        'talks': speaker.talk_set.all(),
    })


@speaker_required
def proposal_talk_details(request, speaker, talk_id):
    talk = get_object_or_404(Talk, site=request.conference.site, speakers__pk=speaker.pk, pk=talk_id)
    return render(request, 'cfp/proposal_talk_details.html', {
        'speaker': speaker,
        'talk': talk,
    })


@speaker_required
def proposal_talk_edit(request, speaker, talk_id=None):
    if talk_id:
        talk = get_object_or_404(Talk, site=request.conference.site, speakers__pk=speaker.pk, pk=talk_id)
    else:
        talk = None
    if is_staff(request, request.user):
        categories = TalkCategory.objects.filter(site=request.conference.site)
    else:
        categories = request.conference.opened_categories
    form = TalkForm(request.POST or None, categories=categories, instance=talk)
    if request.method == 'POST' and form.is_valid():
        talk = form.save(commit=False)
        talk.site = request.conference.site
        talk.save()
        talk.speakers.add(speaker)
        if talk_id:
            messages.success(request, _('Changes saved.'))
        else:
            # TODO: it could be great to receive the proposition by mail
            # but this is not crucial as the speaker already have a link in its mailbox
            messages.success(request, _('You proposition have been successfully submitted!'))
        return redirect(reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)))
    return render(request, 'cfp/proposal_talk_form.html', {
        'speaker': speaker,
        'talk': talk,
        'form': form,
    })


@speaker_required
def proposal_talk_acknowledgment(request, speaker, talk_id, confirm):
    # TODO: handle multiple speakers case
    talk = get_object_or_404(Talk, site=request.conference.site, speakers__pk=speaker.pk, pk=talk_id)
    if not request.conference.disclosed_acceptances or not talk.accepted:
        raise PermissionDenied
    if talk.confirmed == confirm:
        if confirm:
            messages.warning(request, _('You already confirmed your participation to this talk.'))
        else:
            messages.warning(request, _('You already cancelled your participation to this talk.'))
    else:
        talk.confirmed = confirm
        talk.save()
        if confirm:
            confirmation_message= _('Your participation has been taken into account, thank you!')
            thread_note = _('Speaker %(speaker)s confirmed his/her participation.' % {'speaker': speaker})
        else:
            confirmation_message = _('We have noted your unavailability.')
            thread_note = _('Speaker %(speaker)s CANCELLED his/her participation.' % {'speaker': speaker})
        Message.objects.create(thread=talk.conversation, author=speaker, content=thread_note)
        messages.success(request, confirmation_message)
    return redirect(reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)))


# FIXME his this view really useful?
#@speaker_required
#def proposal_speaker_details(request, speaker, talk_id, co_speaker_id):
#    talk = get_object_or_404(Talk, site=request.conference.site, speakers__pk=speaker.pk, pk=talk_id)
#    co_speaker = get_object_or_404(Participant, site=request.conference.site, talk_set__pk=talk.pk, pk=co_speaker_id)
#    return render(request, 'cfp/proposal_speaker_details.html', {
#        'speaker': speaker,
#        'talk': talk,
#        'co_speaker': co_speaker,
#    })


@speaker_required
def proposal_speaker_edit(request, speaker, talk_id=None, co_speaker_id=None):
    talk, co_speaker, co_speaker_candidates = None, None, None
    if talk_id:
        talk = get_object_or_404(Talk, site=request.conference.site, speakers__pk=speaker.pk, pk=talk_id)
        if co_speaker_id:
            co_speaker = get_object_or_404(Participant, site=request.conference.site, talk__pk=talk.pk, pk=co_speaker_id)
        else:
            co_speaker_candidates = speaker.co_speaker_set.exclude(pk__in=talk.speakers.values_list('pk'))
    form = ParticipantForm(request.POST or None, conference=request.conference, instance=co_speaker if talk else speaker)
    if request.method == 'POST' and form.is_valid():
        edited_speaker = form.save()
        if talk:
            talk.speakers.add(edited_speaker)
            #return redirect(reverse('proposal-speaker-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)))
            return redirect(reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)))
        else:
            return redirect(reverse('proposal-dashboard', kwargs=dict(speaker_token=speaker.token)))
    return render(request, 'cfp/proposal_speaker_form.html', {
        'speaker': speaker,
        'talk': talk,
        'co_speaker': co_speaker,
        'co_speaker_candidates': co_speaker_candidates,
        'form': form,
    })


@speaker_required
def proposal_speaker_add(request, speaker, talk_id, speaker_id):
    talk = get_object_or_404(Talk, site=request.conference.site, speakers__pk=speaker.pk, pk=talk_id)
    co_speaker = get_object_or_404(Participant, pk__in=speaker.co_speaker_set.values_list('pk'))
    talk.speakers.add(co_speaker)
    messages.success(request, _('Co-speaker successfully added to the talk.'))
    return redirect(reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk_id)))


# TODO: ask for confirmation (with POST request needed)
@speaker_required
def proposal_speaker_remove(request, speaker, talk_id, co_speaker_id):
    talk = get_object_or_404(Talk, site=request.conference.site, speakers__pk=speaker.pk, pk=talk_id)
    co_speaker = get_object_or_404(Participant, site=request.conference.site, talk__pk=talk.pk, pk=co_speaker_id)
    # prevent speaker from removing his/her self
    if co_speaker.pk == speaker.pk:
        raise PermissionDenied
    talk.speakers.remove(co_speaker)
    messages.success(request, _('Co-speaker successfully removed from the talk.'))
    return redirect(reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk_id)))


# BACKWARD COMPATIBILITY
def talk_proposal(request, talk_id=None, participant_id=None):
    if talk_id and participant_id:
        talk = get_object_or_404(Talk, token=talk_id, site=request.conference.site)
        speaker = get_object_or_404(Participant, token=participant_id, site=request.conference.site)
        return redirect(reverse('proposal-talk-edit', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)))
    else:
        return render(reverse('proposal-home'))


# BACKWARD COMPATIBILITY
def talk_proposal_speaker_edit(request, talk_id, participant_id=None):
    talk = get_object_or_404(Talk, token=talk_id, site=request.conference.site)
    if participant_id:
        speaker = get_object_or_404(Participant, token=participant_id, site=request.conference.site)
        return redirect(reverse('proposal-profile-edit', kwargs=dict(speaker_token=speaker.token)))
    else:
        speaker = talk.speakers.first() # no other choice here…
        return redirect(reverse('proposal-speaker-add', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)))


# TODO: add @staff_required decorator when dropping old links support
def talk_acknowledgment(request, talk_id, confirm, participant_id=None):
    talk = get_object_or_404(Talk, token=talk_id, site=request.conference.site)
    if participant_id:
        speaker = get_object_or_404(Participant, token=participant_id, site=request.conference.site)
        if confirm:
            return redirect(reverse('proposal-talk-confirm', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)))
        else:
            return redirect(reverse('proposal-talk-desist', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)))
    elif not is_staff(request, request.user):
        raise PermissionDenied
    if not talk.accepted or talk.confirmed == confirm:
        raise PermissionDenied
    # TODO: handle multiple speakers case
    talk.confirmed = confirm
    talk.save()
    if confirm:
        confirmation_message= _('The speaker confirmation have been noted.')
        thread_note = _('The talk have been confirmed.')
    else:
        confirmation_message = _('The speaker unavailability have been noted.')
        thread_note = _('The talk have been cancelled.')
    Message.objects.create(thread=talk.conversation, author=request.user, content=thread_note)
    messages.success(request, confirmation_message)
    return redirect(reverse('talk-details', kwargs=dict(talk_id=talk_id)))


@staff_required
def staff(request):
    return render(request, 'cfp/staff/base.html')


@staff_required
def admin(request):
    return render(request, 'cfp/admin/base.html')


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
    try:
        vote = talk.vote_set.get(user=request.user).vote
    except Vote.DoesNotExist:
        vote = None
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
        'vote': vote,
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
def conference_edit(request):
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

    return render(request, 'cfp/admin/conference.html', {
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
    if request.conference.schedule_redirection_url and program_format is None:
        return redirect(request.conference.schedule_redirection_url)
    else:
        return schedule(request, program_format=program_format, pending=False, cache=True, template='cfp/schedule.html')


@staff_required
def staff_schedule(request, program_format):
    return schedule(request, program_format=program_format, pending=True, cache=False, template='cfp/staff/schedule.html')


class Select2View(StaffRequiredMixin, AutoResponseView):
    pass
