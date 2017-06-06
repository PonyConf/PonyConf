
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelform_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, TemplateView

from .models import Participant, Talk


def talk_proposal(request, talk_id=None, participant_id=None):

    site = get_current_site(request)
    talk = None
    participant = None

    if talk_id and participant_id:
        talk = get_object_or_404(Talk, token=talk_id, site=site)
        participant = get_object_or_404(Participant, token=participant_id, site=site)

    ParticipantForm = modelform_factory(Participant, fields=('name','email', 'biography'))
    participant_form = ParticipantForm(request.POST or None, instance=participant)
    TalkForm = modelform_factory(Talk, fields=('category', 'title', 'description','notes'))
    talk_form = TalkForm(request.POST or None, instance=talk)

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
        msg_title = _('Your talk "{}" has been submitted for {}').format(talk.title, site.conference.name)
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

""").format(participant.name, site.conference.name, talk.title, talk.description, url_talk_proposal_edit, url_talk_proposal_speaker_add, url_talk_proposal_speaker_edit, site.conference.name)

        send_mail(
            msg_title,
            msg_body,
            site.conference.from_email(),
            [participant.email],
            fail_silently=False,
        )

        return render(request, 'cfp/complete.html', {'talk': talk, 'participant': participant})

    return render(request, 'cfp/propose.html', {
        'participant_form': participant_form,
        'site': site,
        'talk_form': talk_form,
    })


def talk_proposal_speaker_edit(request, talk_id, participant_id=None):

    site = get_current_site(request)
    talk = get_object_or_404(Talk, token=talk_id, site=site)
    participant = None

    if participant_id:
        participant = get_object_or_404(Participant, token=participant_id, site=site)

    ParticipantForm = modelform_factory(Participant, fields=('name','email', 'biography'))
    participant_form = ParticipantForm(request.POST or None, instance=participant)

    if request.method == 'POST' and participant_form.is_valid():

        participant, created = Participant.objects.get_or_create(email=participant_form.cleaned_data['email'], site=site)
        participant_form = ParticipantForm(request.POST, instance=participant)
        participant = participant_form.save()
        participant.save()

        talk.speakers.add(participant)

        return render(request,'cfp/complete.html', {'talk': talk, 'participant': participant})

    return render(request, 'cfp/speaker.html', {
        'participant_form': participant_form,
        'site': site,
    })

