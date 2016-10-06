from django import forms
from django.contrib.auth.models import User
from django.forms.models import modelform_factory
from django.utils.translation import ugettext_lazy as _

from django_select2.forms import Select2Widget

from .models import Participation, Profile

UserForm = modelform_factory(User, fields=['first_name', 'last_name', 'email', 'username'])

ProfileForm = modelform_factory(Profile, fields=['biography'])

ParticipationForm = modelform_factory(Participation,
                                      fields=['need_transport', 'transport', 'accommodation',
                                              'connector', 'sound', 'videotaped',
                                              'video_licence', 'constraints'],
                                      widgets={'transport': forms.CheckboxSelectMultiple(),
                                               'connector': forms.CheckboxSelectMultiple()},
                                      help_texts = {
                                            'constraints': _('For example, you need to be back on saturday evening, you cannot eat meat.'),
                                      })

ProfileOrgaForm = modelform_factory(Profile, fields=['biography'])

ParticipationOrgaForm = modelform_factory(Participation,
                                          fields=['need_transport', 'transport', 'transport_booked',
                                                  'accommodation', 'accommodation_booked',
                                                  'connector', 'sound', 'videotaped',
                                                  'video_licence',
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
