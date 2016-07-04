from django.forms import CheckboxSelectMultiple
from django.forms.models import modelform_factory

from proposals.models import Talk, Topic

__all__ = ['TalkForm', 'TopicForm', 'TopicOrgaForm']


TalkForm = modelform_factory(Talk, fields=['title', 'description', 'topics', 'event', 'speakers'],
                             widgets={'topics': CheckboxSelectMultiple()})

TopicForm = modelform_factory(Topic, fields=['name'])

TopicOrgaForm = modelform_factory(Topic, fields=['name', 'reviewers'])
