from django import forms
from django.db.utils import OperationalError
from django.forms.models import modelform_factory
from django.utils.translation import ugettext_lazy as _

from django_select2.forms import Select2TagWidget

from accounts.models import User, Participation, Transport
from proposals.models import Conference, Event, Talk, Topic, Track
from planning.models import Room

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
        fields = ['title', 'abstract', 'description', 'topics', 'track', 'notes', 'event', 'speakers', 'duration', 'start_date', 'room', 'registration_required', 'attendees_limit']
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
    room = forms.NullBooleanField(help_text=_('Filter talks already / not yet affected to a room'))
    scheduled = forms.NullBooleanField(help_text=_('Filter talks already / not yet scheduled'))

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super().__init__(*args, **kwargs)
        events = Event.objects.filter(site=site)
        self.fields['kind'].choices = events.values_list('pk', 'name')
        topics = Topic.objects.filter(site=site)
        self.fields['topic'].choices = topics.values_list('slug', 'name')
        tracks = Track.objects.filter(site=site)
        self.fields['track'].choices = [('none', 'Not assigned')] + list(tracks.values_list('slug', 'name'))


class TalkActionForm(forms.Form):
    talks = forms.MultipleChoiceField(choices=[])
    decision = forms.NullBooleanField(label=_('Accept talk?'))
    track = forms.ChoiceField(required=False, choices=[], label=_('Assign to a track'))
    room = forms.ChoiceField(required=False, choices=[], label=_('Put in a room'))

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        talks = kwargs.pop('talks')
        super().__init__(*args, **kwargs)
        self.fields['talks'].choices = [(talk.slug, None) for talk in talks.all()]
        tracks = Track.objects.filter(site=site)
        self.fields['track'].choices = [(None, "---------")] + list(tracks.values_list('slug', 'name'))
        rooms = Room.objects.filter(site=site)
        self.fields['room'].choices = [(None, "---------")] + list(rooms.values_list('slug', 'name'))


def get_options(option):
    try:
        options = list(option.objects.values_list('pk', 'name'))
    except OperationalError:
        # happens when db doesn't exist yet
        options = []
    return options


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
    track = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[],
    )
    transport = forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[('unanswered', 'Not answered'), ('unspecified', 'Not specified')] + get_options(Transport),
    )
    transport_booked = forms.NullBooleanField()
    accommodation= forms.MultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[('unknown', 'Not specified')] + list(Participation.ACCOMMODATION_CHOICES),
    )
    accommodation_booked = forms.NullBooleanField()
    sound = forms.NullBooleanField()

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super().__init__(*args, **kwargs)
        topics = Topic.objects.filter(site=site)
        self.fields['topic'].choices = topics.values_list('slug', 'name')
        tracks = Track.objects.filter(site=site)
        self.fields['track'].choices = [('none', 'Not assigned')] + list(tracks.values_list('slug', 'name'))


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
        if 'instance' in kwargs:
            reviewers = User.objects.filter(topic__track=kwargs['instance'])
            if reviewers.exists():
                self.fields['managers'].help_text = 'Suggestion: ' + ', '.join([str(u) for u in reviewers.all()])

    class Meta:
        model = Track
        fields = ['name', 'description', 'managers']
        widgets = {'managers': Select2TagWidget()}

    def clean_name(self):
        name = self.cleaned_data['name']
        if self.instance and name != self.instance.name and Track.objects.filter(site=self.site, name=name).exists():
            raise self.instance.unique_error_message(self._meta.model, ['name'])
        return name


ConferenceForm = modelform_factory(Conference,
                    fields=['cfp_opening_date', 'cfp_closing_date', 'subscriptions_open', 'venue', 'city', 'home'],
                    widgets={
                        'cfp_opening_date': forms.TextInput(),
                        'cfp_closing_date': forms.TextInput(),
                        'venue': forms.Textarea(attrs={'rows': 4}),
                    })
