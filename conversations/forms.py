from django.forms.models import modelform_factory

from .models import Message

MessageForm = modelform_factory(Message, fields=['content'])
