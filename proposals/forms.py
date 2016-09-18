from django import forms
from django.forms.models import modelform_factory
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from django_select2.forms import Select2TagWidget

from proposals.models import Talk, Topic, Event, Conference


STATUS_CHOICES = [
        ('pending', 'Pending decision'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
]
STATUS_VALUES = [
        ('pending', None),
        ('accepted', True),
        ('declined', False),
]


class TalkForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super(TalkForm, self).__init__(*args, **kwargs)
        self.fields['topics'].queryset = Topic.objects.filter(site=site)
        self.fields['event'].queryset = Event.objects.filter(site=site)

    class Meta:
        model = Talk
        fields = ['title', 'abstract', 'description', 'topics', 'notes', 'event', 'speakers']
        widgets = {'topics': forms.CheckboxSelectMultiple(), 'speakers': Select2TagWidget()}
        help_texts = {
            'abstract': _('Should be less than 255 characters'),
            'notes': _('If you want to add some precisions for the organizers.'),
        }


class FilterForm(forms.Form):
    kind = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[],
    )
    status = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=STATUS_CHOICES,
    )
    topic = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[],
    )
    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super().__init__(*args, **kwargs)
        events = Event.objects.filter(site=site)
        self.fields['kind'].choices = events.values_list('pk', 'name')
        topics = Topic.objects.filter(site=site)
        self.fields['topic'].choices = topics.values_list('slug', 'name')


class TopicCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.site_id = kwargs.pop('site_id')
        super(TopicCreateForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Topic
        fields = ['name', 'description', 'reviewers']
        widgets = {'reviewers': Select2TagWidget()}

    def clean_name(self):
        name = self.cleaned_data['name']
        if name != self.instance.name and Topic.objects.filter(site__id=self.site_id, name=name).exists():
            raise self.instance.unique_error_message(self._meta.model, ['name'])
        return name


TopicUpdateForm = modelform_factory(Topic, fields=['reviewers'],
                                    widgets={'reviewers': Select2TagWidget()})

ConferenceForm = modelform_factory(Conference, fields=['home'])
