from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User

from .forms import ProfileForm, UserForm
from .models import Participation


@login_required
def profile(request):

    forms = [UserForm(request.POST or None, instance=request.user),
             ProfileForm(request.POST or None, instance=request.user.profile)]

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
