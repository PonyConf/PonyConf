from django.core.mail import send_mail
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, TemplateView
from django.contrib import messages

from cfp.decorators import staff_required
from .utils import is_staff
from .models import Participant, Talk, TalkCategory, Vote
from .forms import TalkForm, ParticipantForm


def home(request, conference):
    if conference.home:
        return render(request, 'cfp/home.html')
    else:
        return redirect(reverse('talk-proposal'))


def talk_proposal(request, conference, talk_id=None, participant_id=None):

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

        protocol = 'http' if request.is_secure() else 'http'
        base_url = protocol+'://'+site.domain
        url_talk_proposal_edit = base_url + reverse('talk-proposal-edit', args=[talk.token, participant.token])
        url_talk_proposal_speaker_add = base_url + reverse('talk-proposal-speaker-add', args=[talk.token])
        url_talk_proposal_speaker_edit = base_url + reverse('talk-proposal-speaker-edit', args=[talk.token, participant.token])
        msg_title = _('Your talk "{}" has been submitted for {}').format(talk.title, conference.name)
        msg_body = _("""Hi {},

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

        send_mail(
            msg_title,
            msg_body,
            conference.from_email(),
            [participant.email],
            fail_silently=False,
        )

        return render(request, 'cfp/complete.html', {'talk': talk, 'participant': participant})

    return render(request, 'cfp/propose.html', {
        'participant_form': participant_form,
        'site': site,
        'talk_form': talk_form,
    })


def talk_proposal_speaker_edit(request, conference, talk_id, participant_id=None):

    talk = get_object_or_404(Talk, token=talk_id, site=conference.site)
    participant = None

    if participant_id:
        participant = get_object_or_404(Participant, token=participant_id, site=conference.site)

    participant_form = ParticipantForm(request.POST or None, instance=participant)

    if request.method == 'POST' and participant_form.is_valid():

        participant, created = Participant.objects.get_or_create(email=participant_form.cleaned_data['email'], site=conference.site)
        participant_form = ParticipantForm(request.POST, instance=participant)
        participant = participant_form.save()
        participant.save()

        talk.speakers.add(participant)

        return render(request,'cfp/complete.html', {'talk': talk, 'participant': participant})

    return render(request, 'cfp/speaker.html', {
        'participant_form': participant_form,
    })


@staff_required
def staff(request, conference):
    return render(request, 'cfp/staff/base.html')


@staff_required
def talk_list(request, conference):
    talks = Talk.objects.filter(site=conference.site)
    return render(request, 'cfp/staff/talk_list.html', {
        'talk_list': talks,
    })


@staff_required
def talk_details(request, conference, talk_id):
    talk = get_object_or_404(Talk, token=talk_id, site=conference.site)
    return render(request, 'cfp/staff/talk_details.html', {
        'talk': talk,
    })


@staff_required
def talk_vote(request, conference, talk_id, score):
    talk = get_object_or_404(Talk, token=talk_id, site=conference.site)
    vote, created = Vote.objects.get_or_create(talk=talk, user=request.user)
    vote.vote = int(score)
    vote.save()
    messages.success(request, _('Vote successfully created') if created else _('Vote successfully updated'))
    return redirect(talk.get_absolute_url())


@staff_required
def talk_decide(request, conference, talk_id, accept):
    talk = get_object_or_404(Talk, token=talk_id, site=conference.site)
    if request.method == 'POST':
        # # Does we need to send a notification to the proposer?
        # m = request.POST.get('message', '').strip()
        # if m:
        #     participation = Participation.objects.get(site=site, user=talk.proposer)
        #     conversation = ConversationWithParticipant.objects.get(participation=participation)
        #     Message.objects.create(conversation=conversation, author=request.user, content=m)
        # # Save the decision in the talk's conversation
        # conversation = ConversationAboutTalk.objects.get(talk=talk)
        if accept:
            note = "The talk has been accepted."
        else:
            note = "The talk has been declined."
        #Message.objects.create(conversation=conversation, author=request.user, content=note)
        talk.accepted = accept
        talk.save()
        messages.success(request, _('Decision taken in account'))
        return redirect(talk.get_absolute_url())
    return render(request, 'cfp/staff/talk_decide.html', {
        'talk': talk,
        'accept': accept,
    })


@staff_required
def participant_list(request, conference):
    participants = Participant.objects.filter(site=conference.site)
    return render(request, 'cfp/staff/participant_list.html', {
        'participant_list': participants,
    })


@staff_required
def participant_details(request, conference, participant_id):
    participant = get_object_or_404(Participant, token=participant_id, site=conference.site)
    return render(request, 'cfp/staff/participant_details.html', {
        'participant': participant,
    })
