from django import forms
from django.forms.models import modelform_factory

from .models import Participant, Talk, TalkCategory


class TalkForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        conference = kwargs.pop('conference')
        staff = kwargs.pop('staff')
        super().__init__(*args, **kwargs)
        if staff:
            self.fields['category'].queryset = TalkCategory.objects.filter(site=conference.site)
        else:
            self.fields['category'].queryset = conference.opened_categories

    class Meta:
        model = Talk
        fields = ('category', 'title', 'description','notes')


ParticipantForm = modelform_factory(Participant, fields=('name','email', 'biography'))
