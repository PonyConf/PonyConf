from django import forms
from django.forms.models import modelform_factory

from .models import Participant, Talk


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
