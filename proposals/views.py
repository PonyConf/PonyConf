from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import PonyConfSpeaker, PonyConfUser
from proposals.forms import TalkForm
from proposals.models import Speach, Talk, Topic


def home(request):
    return render(request, 'proposals/home.html')


@login_required
def talk_list(request):
    speaker = PonyConfSpeaker.on_site.filter(user=request.user)
    if speaker.exists():
        speaker = speaker.first()
        mine = Talk.on_site.filter(speakers=speaker)
        others = Talk.on_site.exclude(speakers=speaker)
    else:
        mine = []
        others = Talk.on_site.all()
    return render(request, 'proposals/talks.html', {
        'my_talks': mine,
        'other_talks': others,
    })


@login_required
def talk_list_by_topic(request, topic):
    topic = get_object_or_404(Topic, site=get_current_site(request), slug=topic)
    talks = Talk.objects.filter(topics=topic)
    return render(request, 'proposals/talk_list.html', {
        'title': 'Talks related to %s:' % topic.name,
        'talks': talks,
    })


@login_required
def talk_list_by_speaker(request, speaker):
    speaker = get_object_or_404(PonyConfSpeaker, user__username=speaker)
    talks = Talk.on_site.filter(speakers=speaker)
    return render(request, 'proposals/talk_list.html', {
        'title': 'Talks with %s:' % speaker,
        'talks': talks,
    })


@login_required
def talk_edit(request, talk=None):
    if talk:
        talk = get_object_or_404(Talk, slug=talk)
        if talk.site != get_current_site(request):
            raise PermissionDenied()
        if not request.user.is_superuser and not talk.speakers.filter(user=request.user).exists():
            # FIXME fine permissions
            raise PermissionDenied()
    form = TalkForm(request.POST or None, instance=talk)
    if request.method == 'POST' and form.is_valid():
        if hasattr(talk, 'id'):
            talk = form.save()
            messages.success(request, 'Talk modified successfully!')
        else:
            site = get_current_site(request)
            talk = form.save(commit=False)
            talk.site = site
            talk.save()
            speaker = PonyConfSpeaker.on_site.get_or_create(user=request.user, site=site)[0]
            speach = Speach(speaker=speaker, talk=talk, order=1)
            speach.save()
            messages.success(request, 'Talk proposed successfully!')
        return redirect('show-talk', talk.slug)
    return render(request, 'proposals/talk_edit.html', {
        'form': form,
    })


@login_required
def talk_details(request, talk):
    talk = get_object_or_404(Talk, slug=talk)
    return render(request, 'proposals/talk_details.html', {
        'talk': talk,
    })


@login_required
def topic_list(request):
    topics = Topic.on_site.all()
    return render(request, 'proposals/topic_list.html', {
        'topics': topics,
    })


@login_required
def speaker_list(request):
    speakers = PonyConfSpeaker.on_site.all()
    return render(request, 'proposals/speaker_list.html', {
        'speaker': speakers,
    })


@login_required
def user_details(request, username):
    user = get_object_or_404(PonyConfUser, user__username=username)
    return render(request, 'proposals/user_details.html', {
        'user': user,
    })
