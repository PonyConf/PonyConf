from django import forms
from django.forms.models import modelform_factory
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UsernameField
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.utils.crypto import get_random_string

from django_select2.forms import ModelSelect2MultipleWidget

from .models import Participant, Talk, TalkCategory, Track, Conference


STATUS_CHOICES = [
        ('pending', _('Pending decision')),
        ('accepted', _('Accepted')),
        ('declined', _('Declined')),
]
STATUS_VALUES = [
        ('pending', None),
        ('accepted', True),
        ('declined', False),
]


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


class TalkStaffForm(TalkForm):
    def __init__(self, *args, **kwargs):
        tracks = kwargs.pop('tracks')
        super().__init__(*args, **kwargs)
        self.fields['track'].queryset = tracks

    class Meta(TalkForm.Meta):
        fields = ('category', 'track', 'title', 'description','notes')
        labels = {
            'category': _('Category'),
            'title': _('Title'),
            'description': _('Description'),
            'notes': _('Notes'),
        }
        help_texts = {
            'notes': _('Visible by speakers'),
        }


class TalkFilterForm(forms.Form):
    category = forms.MultipleChoiceField(
            label=_('Category'),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[],
    )
    status = forms.MultipleChoiceField(
            label=_('Status'),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=STATUS_CHOICES,
    )
    track = forms.MultipleChoiceField(
            label=_('Track'),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[],
    )
    vote = forms.NullBooleanField(
            label=_('Vote'),
            help_text=_('Filter talks you already / not yet voted for'),
    )

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super().__init__(*args, **kwargs)
        categories = TalkCategory.objects.filter(site=site)
        self.fields['category'].choices = categories.values_list('pk', 'name')
        tracks = Track.objects.filter(site=site)
        self.fields['track'].choices = [('none', _('Not assigned'))] + list(tracks.values_list('slug', 'name'))


ParticipantForm = modelform_factory(Participant, fields=('name','email', 'biography'))


class UsersWidget(ModelSelect2MultipleWidget):
    model = User
    search_fields = [ '%s__icontains' % field for field in UserAdmin.search_fields ]


class ConferenceForm(forms.ModelForm):
    class Meta:
        model = Conference
        fields = ['name', 'home', 'venue', 'city', 'contact_email', 'reply_email', 'staff',]
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
        user.set_password(get_random_string(length=32))
        if commit:
            user.save()
        return user
