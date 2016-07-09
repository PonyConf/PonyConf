from django.contrib.auth.models import User
from django.forms.models import modelform_factory
from django import forms

from django_select2.forms import Select2Widget

from .models import Participation, Profile

__all__ = ['UserForm', 'ProfileForm', 'ProfileOrgaForm', 'ParticipationOrgaForm']


UserForm = modelform_factory(User, fields=['first_name', 'last_name', 'email', 'username'])

ProfileForm = modelform_factory(Profile, fields=['biography'])

ParticipationForm = modelform_factory(Participation, fields=['transport', 'connector', 'sound', 'videotaped', 'video_licence', 'constraints'])

ProfileOrgaForm = modelform_factory(Profile, fields=['biography', 'notes'])

ParticipationOrgaForm = modelform_factory(Participation,
                                          fields=['transport', 'connector', 'sound', 'videotaped', 'video_licence', 'constraints', 'orga'])

class ParticipationField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.profile.__str__()


class NewParticipationForm(forms.Form):

    participant = ParticipationField(User.objects.all(), widget=Select2Widget(), label='Add participant from existing account')
