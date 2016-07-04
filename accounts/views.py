from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView

from registration.backends.default.views import RegistrationView

from .forms import ParticipationForm, ParticipationOrgaForm, ProfileForm, ProfileOrgaForm, UserForm
from .mixins import StaffRequiredMixin
from .models import Participation, Profile
from .utils import can_edit_profile, is_orga

RESET_PASSWORD_BUTTON = ('password_reset', 'warning', 'Reset your password')
CHANGE_PASSWORD_BUTTON = ('password_change', 'warning', 'Change password')


class Registration(RegistrationView):
    def get_context_data(self, **kwargs):
        return super().get_context_data(buttons=[RESET_PASSWORD_BUTTON], **kwargs)


@login_required
def profile(request):

    forms = [UserForm(request.POST or None, instance=request.user),
             ProfileForm(request.POST or None, instance=request.user.profile),
             ParticipationForm(request.POST or None, instance=Participation.on_site.get(user=request.user))]

    if request.method == 'POST':
        if all(form.is_valid() for form in forms):
            for form in forms:
                form.save()
            messages.success(request, 'Profile updated successfully.')
        else:
            messages.error(request, 'Please correct those errors.')

    return render(request, 'accounts/profile.html', {'forms': forms, 'buttons': [CHANGE_PASSWORD_BUTTON]})


class ParticipantList(StaffRequiredMixin, ListView):
    queryset = Participation.on_site.all()


@login_required
def edit(request, username):

    profile = get_object_or_404(Profile, user__username=username)
    if not can_edit_profile(request, profile):
        raise PermissionDenied()

    participation_form_class = ParticipationOrgaForm if is_orga(request, request.user) else ParticipationForm
    forms = [UserForm(request.POST or None, instance=profile.user),
             ProfileOrgaForm(request.POST or None, instance=profile),
             participation_form_class(request.POST or None, instance=Participation.on_site.get(user=profile.user))]

    if request.method == 'POST':
        if all(form.is_valid() for form in forms):
            for form in forms:
                form.save()
            messages.success(request, 'Profile updated successfully.')
        else:
            messages.error(request, 'Please correct those errors.')

    return render(request, 'accounts/edit_profile.html', {'forms': forms, 'profile': profile})
