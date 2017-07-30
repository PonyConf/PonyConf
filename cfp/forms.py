from django import forms
from django.forms.models import modelform_factory
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

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


ConferenceForm = modelform_factory(Conference, fields=['name', 'home', 'venue', 'city', 'contact_email', 'staff',], widgets={'staff': UsersWidget(),})
