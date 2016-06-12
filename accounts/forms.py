from django.contrib.auth.models import User
from django.forms.models import modelform_factory

from .models import Profile

__all__ = ['UserForm', 'ProfileForm']


UserForm = modelform_factory(User, fields=['first_name', 'last_name', 'email', 'username'])

ProfileForm = modelform_factory(Profile, fields=['biography'])
