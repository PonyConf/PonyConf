from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Participation

from .forms import MessageForm


@login_required
def conversation(request, username=None):

    if username:
        if not request.user.is_superuser:
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
        message = form.save(commit=False)
        message.conversation = conversation
        message.author = request.user
        message.subject = "Assistance request from %s" % message.author.profile
        message.save()
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
def correspondents(request):

    correspondent_list = Participation.on_site.filter(conversation__subscribers=request.user)

    return render(request, 'conversations/correspondents.html', {
            'correspondent_list': correspondent_list,
    })


@login_required
def subscribe(request, username):

    # TODO check admin

    participation = get_object_or_404(Participation, user__username=username, site=get_current_site(request))
    participation.conversation.subscribers.add(request.user)
    messages.success(request, 'Subscribed.')

    next_url = request.GET.get('next') or reverse('conversation', args=[username])

    return redirect(next_url)


@login_required
def unsubscribe(request, username):

    # TODO check admin

    participation = get_object_or_404(Participation, user__username=username, site=get_current_site(request))
    participation.conversation.subscribers.remove(request.user)
    messages.success(request, 'Unsubscribed.')

    next_url = request.GET.get('next') or reverse('conversation', args=[username])

    return redirect(next_url)