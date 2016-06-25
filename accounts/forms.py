from django.contrib.auth.models import User
from django.forms.models import modelform_factory

from .models import Participation, Profile

__all__ = ['UserForm', 'ProfileForm']


UserForm = modelform_factory(User, fields=['first_name', 'last_name', 'email', 'username'])

ParticipationForm = modelform_factory(Participation, fields=['transport', 'connector', 'sound', 'constraints'])

ProfileForm = modelform_factory(Profile, fields=['biography'])
