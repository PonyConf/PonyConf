from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import staff_required
from accounts.models import Participation
from proposals.models import Talk

from .forms import MessageForm


@login_required
def user_conversation(request, username=None):

    if username:
        p = Participation.objects.get(user=request.user, site=get_current_site(request))
        if not p.is_staff() and not p.is_orga():
            raise PermissionDenied()
        user = get_object_or_404(User, username=username)
        template = 'conversations/conversation.html'
    else:
        user = request.user
        template = 'conversations/inbox.html'

    participation = get_object_or_404(Participation, user=user, site=get_current_site(request))
    conversation = participation.conversation
    message_list = conversation.messages.all()

    form = MessageForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.instance.conversation = conversation
        form.instance.author = request.user
        form.save()
        messages.success(request, 'Message sent!')
        if username:
            return redirect(reverse('conversation', args=[username]))
        else:
            return redirect('inbox')

    return render(request, template, {
        'message_list': message_list,
        'form': form,
    })


@login_required
def talk_conversation(request, talk):

    talk = get_object_or_404(Talk, slug=talk)
    form = MessageForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.instance.conversation = talk.conversation
        form.instance.author = request.user
        form.save()
        messages.success(request, 'Message sent!')

    return redirect(talk.get_absolute_url())


@login_required
def correspondents(request):

    correspondent_list = Participation.objects.filter(site=get_current_site(request),
                                                      conversation__subscribers=request.user)

    return render(request, 'conversations/correspondents.html', {
            'correspondent_list': correspondent_list,
    })


@staff_required
def subscribe(request, username):

    participation = get_object_or_404(Participation, user__username=username, site=get_current_site(request))
    participation.conversation.subscribers.add(request.user)
    messages.success(request, 'Subscribed.')

    next_url = request.GET.get('next') or reverse('conversation', args=[username])

    return redirect(next_url)


@staff_required
def unsubscribe(request, username):

    participation = get_object_or_404(Participation, user__username=username, site=get_current_site(request))
    participation.conversation.subscribers.remove(request.user)
    messages.success(request, 'Unsubscribed.')

    next_url = request.GET.get('next') or reverse('conversation', args=[username])

    return redirect(next_url)
