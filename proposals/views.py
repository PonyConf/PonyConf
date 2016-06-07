from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from accounts.models import *
from proposals.models import *
from proposals.forms import *


def home(request):
    return render(request, 'proposals/home.html')

@login_required
def talk_list(request):
    talks = Talk.objects.filter(site=get_current_site(request))
    mine = talks.filter(speakers=request.user)
    others = talks.exclude(speakers=request.user)
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
    speaker = get_object_or_404(User, username=speaker)
    talks = Talk.objects.filter(site=get_current_site(request), speakers=speaker)
    return render(request, 'proposals/talk_list.html', {
        'title': 'Talks with %s:' % (speaker.get_full_name() or speaker.username),
        'talks': talks,
    })

@login_required
def talk_edit(request, talk=None):
    if talk:
        talk = get_object_or_404(Talk, slug=talk)
        if talk.site != get_current_site(request):
            raise PermissionDenied()
        if not request.user.is_superuser and not talk.speakers.filter(username=request.user.username).exists(): # FIXME fine permissions
            raise PermissionDenied()
    form = TalkForm(request.POST or None, instance=talk)
    if request.method == 'POST' and form.is_valid():
        if talk:
            talk = form.save()
            messages.success(request, 'Talk modified successfully!')
        else:
            talk = form.save(commit=False)
            talk.site = get_current_site(request)
            talk.save()
            speach = Speach(user=request.user,talk=talk,order=1)
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
    topics = Topic.objects.filter(site=get_current_site(request))
    return render(request, 'proposals/topic_list.html', {
        'topics': topics,
    })

@login_required
def user_details(request, username):
    user = get_object_or_404(User, username=username)
    return render(request, 'proposals/user_details.html', {
        'user': user,
    })
