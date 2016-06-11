from django.forms.models import modelform_factory

from proposals.models import Talk

__all__ = ['TalkForm']


TalkForm = modelform_factory(Talk, fields=['title', 'description'])
