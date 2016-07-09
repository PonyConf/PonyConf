from django.forms import CheckboxSelectMultiple
from django.forms.models import modelform_factory

from django_select2.forms import Select2TagWidget

from proposals.models import Talk, Topic

__all__ = ['TalkForm', 'TopicCreateForm', 'TopicUpdateForm']


TalkForm = modelform_factory(Talk, fields=['title', 'description', 'topics', 'event', 'speakers'],
                             widgets={'topics': CheckboxSelectMultiple(), 'speakers': Select2TagWidget()})

TopicCreateForm = modelform_factory(Topic, fields=['name', 'reviewers'],
                                    widgets={'reviewers': Select2TagWidget()})

TopicUpdateForm = modelform_factory(Topic, fields=['reviewers'],
                                    widgets={'reviewers': Select2TagWidget()})
