from django import forms
from django.forms.models import modelform_factory
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UsernameField
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify

from django_select2.forms import ModelSelect2MultipleWidget

from .models import Participant, Talk, Conference


class TalkForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        categories = kwargs.pop('categories')
        super().__init__(*args, **kwargs)
        if categories.exists():
            self.fields['category'].queryset = categories
        else:
            del self.fields['category']

    class Meta:
        model = Talk
        fields = ('category', 'title', 'description','notes')


ParticipantForm = modelform_factory(Participant, fields=('name','email', 'biography'))


class UsersWidget(ModelSelect2MultipleWidget):
    model = User
    search_fields = [ '%s__icontains' % field for field in UserAdmin.search_fields ]


class ConferenceForm(forms.ModelForm):
    class Meta:
        model = Conference
        fields = ['name', 'home', 'venue', 'city', 'contact_email', 'staff',]
        widgets = {
            'staff': UsersWidget(),
        }
        help_texts = {
            'staff': _('New staff members will be informed of their new position by e-mail.'),
        }


class CreateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean(self):
        super().clean()
        user = User(first_name=self.cleaned_data.get('first_name'), last_name=self.cleaned_data.get('last_name'))
        username = slugify(user.get_full_name())
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_('An user with that firstname and that lastname already exists.'))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('A user with that email already exists.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = slugify(user.get_full_name())
        user.set_unusable_password()
        if commit:
            user.save()
        return user
