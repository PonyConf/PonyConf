from django.contrib.auth.models import User
from django.forms.models import modelform_factory

from .models import PonyConfUser

__all__ = ['ProfileForm', 'PonyConfUserForm']


ProfileForm = modelform_factory(User, fields=['first_name', 'last_name', 'email', 'username'])

PonyConfUserForm = modelform_factory(PonyConfUser, fields=['biography'])
