from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import PonyConfUserForm, ProfileForm


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
