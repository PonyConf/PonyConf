from django import forms
from django.contrib.auth.models import User
from django.forms.models import modelform_factory

from django_select2.forms import Select2Widget

from .models import Participation, Profile

UserForm = modelform_factory(User, fields=['first_name', 'last_name', 'email', 'username'])

ProfileForm = modelform_factory(Profile, fields=['biography'])

ParticipationForm = modelform_factory(Participation, fields=['transport', 'connector', 'sound', 'videotaped',
                                                             'video_licence', 'constraints'],
                                      widgets={'transport': forms.CheckboxSelectMultiple(),
                                               'connector': forms.CheckboxSelectMultiple()})

ProfileOrgaForm = modelform_factory(Profile, fields=['biography'])

ParticipationOrgaForm = modelform_factory(Participation,
                                          fields=['transport', 'connector', 'sound', 'videotaped', 'video_licence',
                                                  'constraints', 'notes', 'orga'],
                                          widgets={'transport': forms.CheckboxSelectMultiple(),
                                                   'connector': forms.CheckboxSelectMultiple()})


class ParticipationField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.profile.__str__()


class NewParticipationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super().__init__(*args, **kwargs)
        queryset = User.objects.exclude(participation__site=site).all()
        self.fields['participant'] = ParticipationField(queryset, widget=Select2Widget(),
                                     label='Add participant from existing account')
