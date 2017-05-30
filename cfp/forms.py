from django import forms
from django.forms.models import modelform_factory

from .models import Participant, Talk


class ProposeForm(forms.Form):
    pass


ParticipantForm = modelform_factory(Participant, fields=['email'])
TalkForm = modelform_factory(Talk, fields=['title'])
