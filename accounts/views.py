from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render

from .forms import ProfileForm, UserForm, ParticipationForm
from .models import Participation


@login_required
def profile(request):

    forms = [UserForm(request.POST or None, instance=request.user),
             ProfileForm(request.POST or None, instance=request.user.profile),
             ParticipationForm(request.POST or None, instance=Participation.on_site.get(user=request.user)),
             ]

    if request.method == 'POST':
        if all(form.is_valid() for form in forms):
            for form in forms:
                form.save()
            messages.success(request, 'Profile updated successfully.')
        else:
            messages.error(request, 'Please correct those errors.')

    return render(request, 'accounts/profile.html', {'forms': forms})


@login_required
def participants(request):

    if not request.user.is_superuser:
        raise PermissionDenied()

    participation_list = Participation.on_site.all()

    return render(request, 'admin/participants.html', {'participation_list': participation_list})


def participant(request, username):
    return render(request, 'admin/participant.html',
                  {'participant': get_object_or_404(Participation, user__username=username)})
