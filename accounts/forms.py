from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.forms.models import modelform_factory


from .models import User, Profile


# email MUST be validated, we do not allow to edit it
UserForm = modelform_factory(User, fields=['first_name', 'last_name', 'username'])

ProfileForm = modelform_factory(Profile, fields=[
                    'phone_number', 'biography', 'twitter', 'website',
                    'linkedin', 'facebook', 'mastodon'])


class EmailAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = _('Email address')
