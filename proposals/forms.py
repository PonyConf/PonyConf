from django import forms
from django.forms.models import modelform_factory
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from django_select2.forms import Select2TagWidget

from proposals.models import Talk, Topic, Track, Event, Conference

from accounts.models import Transport


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
        self.fields['track'].queryset = Track.objects.filter(site=site)
        self.fields['event'].queryset = Event.objects.filter(site=site)

    class Meta:
        model = Talk
        fields = ['title', 'abstract', 'description', 'topics', 'track', 'notes', 'event', 'speakers']
        widgets = {'topics': forms.CheckboxSelectMultiple(), 'speakers': Select2TagWidget()}
        help_texts = {
            'abstract': _('Should be less than 255 characters'),
            'notes': _('If you want to add some precisions for the organizers.'),
        }


class TalkFilterForm(forms.Form):
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
    track = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[],
    )
    vote = forms.NullBooleanField(help_text=_('Filter talks you already / not yet voted for'))

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super().__init__(*args, **kwargs)
        events = Event.objects.filter(site=site)
        self.fields['kind'].choices = events.values_list('pk', 'name')
        topics = Topic.objects.filter(site=site)
        self.fields['topic'].choices = topics.values_list('slug', 'name')
        tracks = Track.objects.filter(site=site)
        self.fields['track'].choices = [('none', 'Not assigned')] + list(tracks.values_list('slug', 'name'))


class SpeakerFilterForm(forms.Form):
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
    transport = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=Transport.objects.values_list('pk', 'name'),
    )
    hosting = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[
                    ('hotel', 'Hotel'),
                    ('homestay', 'Homestay'),
            ],
    )
    sound = forms.NullBooleanField()

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super().__init__(*args, **kwargs)
        topics = Topic.objects.filter(site=site)
        self.fields['topic'].choices = topics.values_list('slug', 'name')


class TopicForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.site = kwargs.pop('site')
        super().__init__(*args, **kwargs)
        self.fields['track'].queryset = Track.objects.filter(site=self.site)

    class Meta:
        model = Topic
        fields = ['name', 'description', 'reviewers', 'track']
        widgets = {'reviewers': Select2TagWidget()}

    def clean_name(self):
        name = self.cleaned_data['name']
        if self.instance and name != self.instance.name and Topic.objects.filter(site=self.site, name=name).exists():
            raise self.instance.unique_error_message(self._meta.model, ['name'])
        return name


class TrackForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.site = kwargs.pop('site')
        super().__init__(*args, **kwargs)

    class Meta:
        model = Track
        fields = ['name', 'description']

    def clean_name(self):
        name = self.cleaned_data['name']
        if self.instance and name != self.instance.name and Track.objects.filter(site=self.site, name=name).exists():
            raise self.instance.unique_error_message(self._meta.model, ['name'])
        return name


ConferenceForm = modelform_factory(Conference, fields=['cfp_opening_date', 'cfp_closing_date', 'home'])
