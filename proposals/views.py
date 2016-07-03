from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, DetailView, ListView

from accounts.mixins import StaffRequiredMixin
from accounts.models import Participation

from .forms import TalkForm
from .models import Talk, Topic, Vote
from .signals import new_talk
from .utils import allowed_talks


def home(request):
    return render(request, 'proposals/home.html')


@login_required
def talk_list(request):
    return render(request, 'proposals/talks.html', {
        'my_talks': Talk.on_site.filter(Q(speakers=request.user) | Q(proposer=request.user)),
        'other_talks': allowed_talks(Talk.on_site.exclude(speakers=request.user, proposer=request.user), request)
    })


@login_required
def talk_list_by_topic(request, topic):
    topic = get_object_or_404(Topic, slug=topic)
    talks = allowed_talks(Talk.on_site.filter(topics=topic), request)
    return render(request, 'proposals/talk_list.html', {'title': 'Talks related to %s:' % topic, 'talk_list': talks})


@login_required
def talk_list_by_speaker(request, speaker):
    speaker = get_object_or_404(User, username=speaker)
    talks = allowed_talks(Talk.on_site.filter(speakers=speaker), request)
    return render(request, 'proposals/talk_list.html', {'title': 'Talks with %s:' % speaker, 'talk_list': talks})


@login_required
def talk_edit(request, talk=None):
    if talk:
        talk = get_object_or_404(Talk, slug=talk, site=get_current_site(request))
        if not talk.is_editable_by(request.user):
            raise PermissionDenied()
    form = TalkForm(request.POST or None, instance=talk)
    if talk:
        form.fields['title'].disabled = True
        form.fields['topics'].disabled = True
    else:
        form.fields['speakers'].initial = [request.user]
    if request.method == 'POST' and form.is_valid():
        if hasattr(talk, 'id'):
            talk = form.save()
            messages.success(request, 'Talk modified successfully!')
        else:
            form.instance.site = get_current_site(request)
            form.instance.proposer = request.user
            talk = form.save()
            new_talk.send(talk.__class__, instance=talk)
            messages.success(request, 'Talk proposed successfully!')
        return redirect(talk.get_absolute_url())
    return render(request, 'proposals/talk_edit.html', {
        'form': form,
    })


class TalkDetail(LoginRequiredMixin, DetailView):
    queryset = Talk.on_site.all()

    def get_context_data(self, **ctx):
        user = self.request.user
        if self.object.is_moderable_by(user):
            vote = Vote.objects.filter(talk=self.object, user=Participation.on_site.get(user=user)).first()
            ctx.update(edit_perm=True, moderate_perm=True, vote=vote,
                       form_url=reverse('talk-conversation', kwargs={'talk': self.object.slug}))
        else:
            ctx['edit_perm'] = self.object.is_editable_by(user)
        return super().get_context_data(**ctx)


class TopicList(LoginRequiredMixin, ListView):
    model = Topic


class TopicCreate(StaffRequiredMixin, CreateView):
    model = Topic
    fields = ['name']


class SpeakerList(StaffRequiredMixin, ListView):
    queryset = User.objects.filter(talk__in=Talk.on_site.all()).distinct()
    template_name = 'proposals/speaker_list.html'


@login_required
def vote(request, talk, score):
    site = get_current_site(request)
    talk = get_object_or_404(Talk, site=site, slug=talk)
    user = Participation.on_site.get(user=request.user)
    if not talk.is_moderable_by(request.user):
        raise PermissionDenied()
    vote, created = Vote.objects.get_or_create(talk=talk, user=user)
    vote.vote = int(score)
    vote.save()
    messages.success(request, "Vote successfully %s" % ('created' if created else 'updated'))
    return redirect(talk.get_absolute_url())


@login_required
def user_details(request, username):
    return render(request, 'proposals/user_details.html', {
        'profile': get_object_or_404(User, username=username).profile,
    })
