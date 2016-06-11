from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import password_change
from django.contrib import messages

from .forms import ProfileForm, PonyConfUserForm


@login_required
def password(request):
    return password_change(request, post_change_redirect='profile')


@login_required
def profile(request):

    forms = [ProfileForm(request.POST or None, instance=request.user),
             PonyConfUserForm(request.POST or None, instance=request.user.ponyconfuser)]

    if request.method == 'POST':
        if all(form.is_valid() for form in forms):
            for form in forms:
                form.save()
            messages.success(request, 'Profile updated successfully.')
        else:
            messages.error(request, 'Please correct those errors.')

    return render(request, 'accounts/profile.html', {'forms': forms})
