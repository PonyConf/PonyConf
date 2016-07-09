from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from accounts.mixins import OrgaRequiredMixin, StaffRequiredMixin, SuperuserRequiredMixin
from accounts.models import Participation
from accounts.utils import is_orga

from .forms import TalkForm, TopicCreateForm, TopicUpdateForm
from .models import Talk, Topic, Vote
from .utils import allowed_talks
from .signals import *


def home(request):
    return render(request, 'proposals/home.html')


@login_required
def talk_list(request):
    return render(request, 'proposals/talks.html', {
        'my_talks': Talk.objects.filter(site=get_current_site(request)).filter(Q(speakers=request.user) | Q(proposer=request.user)).distinct(),
        'other_talks': allowed_talks(Talk.objects.filter(site=get_current_site(request)).exclude(speakers=request.user, proposer=request.user), request)
    })


@login_required
def talk_list_by_topic(request, topic):
    topic = get_object_or_404(Topic, slug=topic)
    talks = allowed_talks(Talk.objects.filter(site=topic.site, topics=topic), request)
    return render(request, 'proposals/talk_list.html', {'title': 'Talks related to %s:' % topic, 'talk_list': talks})


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
            talk_edited.send(talk.__class__, instance=talk, author=request.user)
            messages.success(request, 'Talk modified successfully!')
        else:
            form.instance.site = get_current_site(request)
            form.instance.proposer = request.user
            talk = form.save()
            talk_added.send(talk.__class__, instance=talk, author=request.user)
            messages.success(request, 'Talk proposed successfully!')
        return redirect(talk.get_absolute_url())
    return render(request, 'proposals/talk_edit.html', {
        'form': form,
    })


class TalkDetail(LoginRequiredMixin, DetailView):
    def get_queryset(self):
        return Talk.objects.filter(site=get_current_site(self.request)).all()

    def get_context_data(self, **ctx):
        user = self.request.user
        if self.object.is_moderable_by(user):
            vote = Vote.objects.filter(talk=self.object, user=Participation.objects.get(site=get_current_site(self.request), user=user)).first()
            ctx.update(edit_perm=True, moderate_perm=True, vote=vote,
                       form_url=reverse('talk-conversation', kwargs={'talk': self.object.slug}))
        else:
            ctx['edit_perm'] = self.object.is_editable_by(user)
        return super().get_context_data(**ctx)


class TopicMixin(object):
    model = Topic

    def get_queryset(self):
        return Topic.objects.filter(site=get_current_site(self.request)).all()


class TopicList(LoginRequiredMixin, TopicMixin, ListView):
    pass


class TopicCreate(OrgaRequiredMixin, TopicMixin, CreateView):
    form_class = TopicCreateForm
    def form_valid(self, form):
        form.instance.site = get_current_site(self.request)
        return super(TopicCreate, self).form_valid(form)


class TopicUpdate(OrgaRequiredMixin, TopicMixin, UpdateView):
    def get_form_class(self):
        return TopicCreateForm if self.request.user.is_superuser else TopicUpdateForm


class SpeakerList(StaffRequiredMixin, ListView):
    template_name = 'proposals/speaker_list.html'

    def get_queryset(self):
        current_site = get_current_site(request)
        return User.objects.filter(talk__in=Talk.objects.filter(site=current_site)).all().distinct()


@login_required
def vote(request, talk, score):
    current_site = get_current_site(request)
    talk = get_object_or_404(Talk, site=current_site, slug=talk)
    user = Participation.objects.get(site=current_site, user=request.user)
    if not talk.is_moderable_by(request.user):
        raise PermissionDenied()
    vote, created = Vote.objects.get_or_create(talk=talk, user=user)
    vote.vote = int(score)
    vote.save()
    messages.success(request, "Vote successfully %s" % ('created' if created else 'updated'))
    return redirect(talk.get_absolute_url())


@login_required
def user_details(request, username):
    speaker = get_object_or_404(User, username=username)
    return render(request, 'proposals/user_details.html', {
        'profile': speaker.profile,
        'talk_list': allowed_talks(Talk.objects.filter(site=get_current_site(request), speakers=speaker), request),
    })
