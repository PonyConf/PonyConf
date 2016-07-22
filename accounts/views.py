from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import staff_required
from .forms import (NewParticipationForm, ParticipationForm,
                    ParticipationOrgaForm, ProfileForm, ProfileOrgaForm, UserForm)
from .models import Participation, Profile, User
from .utils import can_edit_profile, is_orga

RESET_PASSWORD_BUTTON = ('password_reset', 'warning', 'Reset your password')
CHANGE_PASSWORD_BUTTON = ('password_change', 'warning', 'Change password')


@login_required
def profile(request):

    forms = [UserForm(request.POST or None, instance=request.user),
             ProfileForm(request.POST or None, instance=request.user.profile),
             ParticipationForm(request.POST or None, instance=Participation.objects.get(site=get_current_site(request),
                                                                                        user=request.user))]

    if request.method == 'POST':
        if all(form.is_valid() for form in forms):
            for form in forms:
                form.save()
            messages.success(request, 'Profile updated successfully.')
        else:
            messages.error(request, 'Please correct those errors.')

    return render(request, 'accounts/profile.html', {'forms': forms, 'buttons': [CHANGE_PASSWORD_BUTTON]})


@staff_required
def participation_list(request):
    participation_list = Participation.objects.filter(site=get_current_site(request)).all()
    form = NewParticipationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        if not Participation.objects.get(user=request.user, site=get_current_site(request)).is_orga():
            raise PermissionDenied()
        user = User.objects.get(username=form.cleaned_data['participant'])
        participation, created = Participation.objects.get_or_create(user=user, site=get_current_site(request))
        if created:
            messages.success(request, "%s added to participant" % user.profile)
        else:
            messages.info(request, "%s is already a participant" % user.profile)
        return redirect(reverse('list-participant'))

    return render(request, 'accounts/participation_list.html', {
        'participation_list': participation_list,
        'form': form,
    })


@login_required
def edit(request, username):

    profile = get_object_or_404(Profile, user__username=username)
    if not can_edit_profile(request, profile):
        raise PermissionDenied()

    participation_form = ParticipationOrgaForm if is_orga(request, request.user) else ParticipationForm
    forms = [UserForm(request.POST or None, instance=profile.user),
             ProfileOrgaForm(request.POST or None, instance=profile),
             participation_form(request.POST or None,
                                instance=Participation.objects.get(site=get_current_site(request), user=profile.user))]

    if request.method == 'POST':
        if all(form.is_valid() for form in forms):
            for form in forms:
                form.save()
            messages.success(request, 'Profile updated successfully.')
        else:
            messages.error(request, 'Please correct those errors.')

    return render(request, 'accounts/edit_profile.html', {'forms': forms, 'profile': profile})
