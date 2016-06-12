from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import ProfileForm, UserForm


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
