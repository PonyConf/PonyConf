from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.utils.translation import ugettext as _
from django.shortcuts import redirect, render
from django.contrib import messages

from accounts.models import User, Profile
from accounts.forms import UserForm, ProfileForm, EmailAuthenticationForm


RESET_PASSWORD_BUTTON = ('password_reset', 'warning', _('Reset your password'))
CHANGE_PASSWORD_BUTTON = ('password_change', 'warning', _('Change password'))


class EmailLoginView(LoginView):
    authentication_form = EmailAuthenticationForm


@login_required
def profile(request):
    user_form = UserForm(request.POST or None, instance=request.user)
    profile_form = ProfileForm(request.POST or None, instance=request.user.profile)
    forms = [user_form, profile_form]
    if request.method == 'POST':
        if all(map(lambda form: form.is_valid(), forms)):
            for form in forms:
                form.save()
            messages.success(request, _('Profile updated successfully.'))
        else:
            messages.error(request, _('Please correct those errors.'))
    return render(request, 'accounts/profile.html', {
        'forms': forms,
        'buttons': [CHANGE_PASSWORD_BUTTON],
    })
