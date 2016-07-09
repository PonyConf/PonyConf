from django.forms import CheckboxSelectMultiple
from django.forms.models import modelform_factory

from proposals.models import Talk, Topic

__all__ = ['TalkForm', 'TopicCreateForm', 'TopicUpdateForm']


TalkForm = modelform_factory(Talk, fields=['title', 'description', 'topics', 'event', 'speakers'],
                             widgets={'topics': CheckboxSelectMultiple()})

TopicCreateForm = modelform_factory(Topic, fields=['name', 'reviewers'])

TopicUpdateForm = modelform_factory(Topic, fields=['reviewers'])
