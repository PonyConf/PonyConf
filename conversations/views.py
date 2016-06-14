from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.contrib import messages


from accounts.models import Participation
from .models import Message
from .forms import MessageForm


@login_required
def messaging(request):

    participation = get_object_or_404(Participation, user=request.user, site=get_current_site(request))
    conversation = participation.conversation
    message_list = conversation.messages.all()

    form = MessageForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.author = request.user
        message.save()
        messages.success(request, 'Message sent!')
        return redirect('messaging')

    return render(request, 'conversations/messaging.html', {
        'message_list': message_list,
        'form': form,
    })
