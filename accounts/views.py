from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages

from accounts.forms import *


@login_required
def profile(request):
    profileform = None
    passwordform = None

    if request.method == 'POST':
        if 'update-profile' in request.POST:
            profileform = ProfileForm(request.POST, instance=request.user)
            if profileform.is_valid():
                profileform.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('profile')
        elif 'update-password' in request.POST:
            passwordform = PasswordChangeForm(user=request.user, data=request.POST)
            if passwordform.is_valid():
                passwordform.save()
                messages.success(request, 'Password updated successfully.')
                return redirect('profile')

    if not profileform:
        profileform = ProfileForm(None, instance=request.user)
    if not passwordform:
        passwordform = PasswordChangeForm(None)

    return render(request, 'accounts/profile.html', {
        'profileform': profileform,
        'passwordform': passwordform,
    })
