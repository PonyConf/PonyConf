from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView

from registration.backends.default.views import RegistrationView

from .forms import ParticipationForm, ProfileForm, ProfileOrgaForm, UserForm
from .mixins import StaffRequiredMixin
from .models import Participation, Profile
from .utils import can_edit_profile

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


def participant(request, username):
    return render(request, 'admin/participant.html',
                  {'participant': get_object_or_404(Participation, user__username=username)})


@login_required
def edit(request, username):

    profile = get_object_or_404(Profile, user__username=username)
    if not can_edit_profile(request, profile):
        raise PermissionDenied()

    form = ProfileOrgaForm(request.POST or None, instance=profile)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
        else:
            messages.error(request, 'Please correct those errors.')

    return render(request, 'accounts/edit_profile.html', {'form': form, 'profile': profile})
