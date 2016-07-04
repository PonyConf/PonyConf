from django.contrib.auth.models import User
from django.forms.models import modelform_factory

from .models import Participation, Profile

__all__ = ['UserForm', 'ProfileForm', 'ProfileOrgaForm', 'ParticipationOrgaForm']


UserForm = modelform_factory(User, fields=['first_name', 'last_name', 'email', 'username'])

ProfileForm = modelform_factory(Profile, fields=['biography'])

ParticipationForm = modelform_factory(Participation, fields=['transport', 'connector', 'sound', 'constraints'])

ProfileOrgaForm = modelform_factory(Profile, fields=['biography', 'notes'])

ParticipationOrgaForm = modelform_factory(Participation,
                                          fields=['transport', 'connector', 'sound', 'constraints', 'orga'])
