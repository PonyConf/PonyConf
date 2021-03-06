from django import forms
from django.forms.models import modelform_factory
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UsernameField
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from django.template.defaultfilters import slugify
from django.utils.crypto import get_random_string

from django_select2.forms import ModelSelect2MultipleWidget

from .models import Participant, Talk, TalkCategory, Track, Tag, \
                    Conference, Room, Volunteer, Activity
from .environment import TalkEnvironment, SpeakerEnvironment, VolunteerEnvironment


ACCEPTATION_CHOICES = [
        ('pending', _('Pending decision')),
        ('accepted', _('Accepted')),
        ('declined', _('Declined')),
]
ACCEPTATION_VALUES = [
        ('pending', None),
        ('accepted', True),
        ('declined', False),
]

CONFIRMATION_CHOICES = [
        ('waiting', _('Waiting')),
        ('confirmed', _('Confirmed')),
        ('cancelled', _('Cancelled')),
]
CONFIRMATION_VALUES = [
        ('waiting', None),
        ('confirmed', True),
        ('cancelled', False),
]


class OnSiteNamedModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.conference = kwargs.pop('conference')
        super().__init__(*args, **kwargs)

    # we should manually check (site, name) uniqueness as the site is not part of the form
    def clean_name(self):
        name = self.cleaned_data['name']
        if (not self.instance or self.instance.name != name) \
                and self._meta.model.objects.filter(site=self.conference.site, name=name).exists():
            raise self.instance.unique_error_message(self._meta.model, ['name'])
        return name

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.site = self.conference.site
        if commit:
            obj.save()
        return obj


class VolunteerFilterForm(forms.Form):
    activity = forms.MultipleChoiceField(
               label=_('Activity'),
               required=False,
               widget=forms.CheckboxSelectMultiple,
               choices=[],
   )

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super().__init__(*args, **kwargs)
        activities = Activity.objects.filter(site=site)
        self.fields['activity'].choices = [('none', pgettext_lazy('activity', 'None'))] + list(activities.values_list('slug', 'name'))


class TalkForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        categories = kwargs.pop('categories')
        super().__init__(*args, **kwargs)
        if kwargs.get('instance', None):
            del self.fields['category']
        else:
            self.fields['category'].queryset = categories
        if self.instance and self.instance.accepted is not True:
            del self.fields['materials']

    class Meta:
        model = Talk
        fields = ('category', 'title', 'description', 'notes', 'materials',)


class TalkStaffForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        conference = kwargs.pop('conference')
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = TalkCategory.objects.filter(site=conference.site)
        self.fields['track'].queryset = Track.objects.filter(site=conference.site)
        self.fields['room'].queryset = Room.objects.filter(site=conference.site)
        if self.instance and self.instance.category and self.instance.category.duration:
            self.fields['duration'].help_text = _('Default duration: %(duration)d min') % {'duration': self.instance.duration}

    class Meta(TalkForm.Meta):
        fields = ('category', 'track', 'title', 'description', 'notes', 'tags', 'start_date', 'duration', 'room', 'materials', 'video', 'speakers')
        widgets = {
            'tags': forms.CheckboxSelectMultiple,
        }
        labels = {
            'category': _('Category'),
            'title': _('Title'),
            'description': _('Description'),
            'notes': _('Notes'),
        }
        help_texts = {
            'notes': _('Visible by speakers'),
        }


class TalkFilterForm(forms.Form):
    category = forms.MultipleChoiceField(
            label=_('Category'),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[],
    )
    accepted = forms.MultipleChoiceField(
            label=_('Accepted'),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=ACCEPTATION_CHOICES,
    )
    confirmed = forms.MultipleChoiceField(
            label=_('Confirmed'),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=CONFIRMATION_CHOICES,
    )
    track = forms.MultipleChoiceField(
            label=_('Track'),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[],
    )
    tag = forms.MultipleChoiceField(
            label=_('Tag'),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[],
    )
    vote = forms.NullBooleanField(
            label=_('Vote'),
            help_text=_('Filter talks you already / not yet voted for'),
    )
    room = forms.NullBooleanField(
            label=_('Room'),
            help_text=_('Filter talks already / not yet affected to a room'),
    )
    scheduled = forms.NullBooleanField(
            label=_('Scheduled'),
            help_text=_('Filter talks already / not yet scheduled'),
    )
    materials = forms.NullBooleanField(
            label=_('Materials'),
            help_text=_('Filter talks with / without materials'),
    )
    video = forms.NullBooleanField(
            label=_('Video'),
            help_text=_('Filter talks with / without video'),
    )

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super().__init__(*args, **kwargs)
        categories = TalkCategory.objects.filter(site=site)
        self.fields['category'].choices = categories.values_list('pk', 'name')
        tracks = Track.objects.filter(site=site)
        self.fields['track'].choices = [('none', _('Not assigned'))] + list(tracks.values_list('slug', 'name'))
        self.fields['tag'].choices = Tag.objects.filter(site=site).values_list('slug', 'name')


class TalkActionForm(forms.Form):
    EMAIL_TALKS = 1
    EMAIL_SPEAKERS = 2
    EMAIL_CHOICES = (
        (None, "---------"),
        (EMAIL_TALKS, _('one per speaker and talk combination')),
        (EMAIL_SPEAKERS, _('only one per speaker')),
    )

    talks = forms.MultipleChoiceField(choices=[])
    decision = forms.NullBooleanField(label=_('Accept talk?'))
    track = forms.ChoiceField(required=False, choices=[], label=_('Assign to a track'))
    tag = forms.ChoiceField(required=False, choices=[], label=_('Add a tag'))
    room = forms.ChoiceField(required=False, choices=[], label=_('Put in a room'))
    email = forms.ChoiceField(required=False, choices=EMAIL_CHOICES, label=_('Send an email'))

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        talks = kwargs.pop('talks')
        super().__init__(*args, **kwargs)
        self.fields['talks'].choices = [(talk.pk, None) for talk in talks.all()]
        tracks = Track.objects.filter(site=site)
        self.fields['track'].choices = [(None, "---------")] + list(tracks.values_list('slug', 'name'))
        tags = Tag.objects.filter(site=site)
        self.fields['tag'].choices = [(None, "---------")] + list(tags.values_list('slug', 'name'))
        rooms = Room.objects.filter(site=site)
        self.fields['room'].choices = [(None, "---------")] + list(rooms.values_list('slug', 'name'))


class SpeakerActionForm(forms.Form):
    speakers = forms.MultipleChoiceField(choices=[])
    email = forms.BooleanField(required=False, label=_('Send an email'))

    def __init__(self, *args, **kwargs):
        speakers = kwargs.pop('speakers')
        super().__init__(*args, **kwargs)
        self.fields['speakers'].choices = [(speaker.pk, None) for speaker in speakers.all()]


class VolunteerActionForm(forms.Form):
    volunteers = forms.MultipleChoiceField(choices=[])
    email = forms.BooleanField(required=False, label=_('Send an email'))

    def __init__(self, *args, **kwargs):
        volunteers = kwargs.pop('volunteers')
        super().__init__(*args, **kwargs)
        self.fields['volunteers'].choices = [(volunteer.pk, None) for volunteer in volunteers.all()]


class NotifyForm(forms.Form):
    notify = forms.BooleanField(initial=True, required=False, label=_('Notify by mail?'))


class ParticipantForm(OnSiteNamedModelForm):
    SOCIAL_FIELDS = ['twitter', 'linkedin', 'github', 'website', 'facebook', 'mastodon']

    def clean_email(self):
        email = self.cleaned_data['email']
        if (not self.instance or self.instance.email != email) \
                and self._meta.model.objects.filter(site=self.conference.site, email=email).exists():
            raise self.instance.unique_error_message(self._meta.model, ['email'])
        return email


class ParticipantFilterForm(forms.Form):
    category = forms.MultipleChoiceField(
            label=_('Category'),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[],
    )
    accepted = forms.MultipleChoiceField(
            label=_('Accepted'),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=ACCEPTATION_CHOICES,
    )
    confirmed = forms.MultipleChoiceField(
            label=_('Confirmed'),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=CONFIRMATION_CHOICES,
    )
    track = forms.MultipleChoiceField(
            label=_('Track'),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            choices=[],
    )

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super().__init__(*args, **kwargs)
        categories = TalkCategory.objects.filter(site=site)
        self.fields['category'].choices = categories.values_list('pk', 'name')
        tracks = Track.objects.filter(site=site)
        self.fields['track'].choices = [('none', _('Not assigned'))] + list(tracks.values_list('slug', 'name'))


class EmailForm(forms.Form):
    email = forms.EmailField(required=True, label=_('Email'))


class PreviewTalkMailForm(forms.Form):
    speaker = forms.IntegerField()
    talk = forms.IntegerField()
    subject = forms.CharField(required=False, label=_('Subject'))
    body = forms.CharField(required=False, label=_('Body'))


class PreviewSpeakerMailForm(forms.Form):
    speaker = forms.IntegerField()
    subject = forms.CharField(required=False, label=_('Subject'))
    body = forms.CharField(required=False, label=_('Body'))


class PreviewVolunteerMailForm(forms.Form):
    volunteer = forms.IntegerField()
    subject = forms.CharField(required=False, label=_('Subject'))
    body = forms.CharField(required=False, label=_('Body'))


class SendMailForm(forms.Form):
    subject = forms.CharField()
    body = forms.CharField(widget=forms.Textarea)
    confirm = forms.BooleanField(required=False, label=_('I read my self twice, confirm sending'))

    def clean_subject(self):
        return self.clean_template('subject')

    def clean_body(self):
        return self.clean_template('body')



class SendTalkMailForm(SendMailForm):
    def __init__(self, *args, **kwargs):
        self._talks = kwargs.pop('talks')
        super().__init__(*args, **kwargs)
        self._env = dict()

    def clean_template(self, template):
        try:
            for talk in self._talks.all():
                for speaker in talk.speakers.all():
                    env = self._env.get((talk, speaker), TalkEnvironment(talk, speaker))
                    env.from_string(self.cleaned_data.get(template)).render()
        except Exception as e:
            raise forms.ValidationError(_("Your template does not compile (at least) with talk '%(talk)s' and speaker '%(speaker)s'.") %
                        {'talk': talk, 'speaker': speaker})
        return self.cleaned_data.get(template)


class SendSpeakerMailForm(SendMailForm):
    def __init__(self, *args, **kwargs):
        self._speakers = kwargs.pop('speakers')
        super().__init__(*args, **kwargs)
        self._env = dict()

    def clean_template(self, template):
        try:
            for speaker in self._speakers.all():
                env = self._env.get(speaker, SpeakerEnvironment(speaker))
                env.from_string(self.cleaned_data.get(template)).render()
        except Exception as e:
            raise forms.ValidationError(_("Your template does not compile (at least) with speaker '%(speaker)s'.") %
                        {'speaker': speaker})
        return self.cleaned_data.get(template)


class SendVolunteerMailForm(SendMailForm):
    def __init__(self, *args, **kwargs):
        self._volunteers = kwargs.pop('volunteers')
        super().__init__(*args, **kwargs)
        self._env = dict()

    def clean_template(self, template):
        try:
            for volunteer in self._volunteers.all():
                env = self._env.get(volunteer, VolunteerEnvironment(volunteer))
                env.from_string(self.cleaned_data.get(template)).render()
        except Exception as e:
            raise forms.ValidationError(_("Your template does not compile (at least) with volunteer '%(volunteer)s'.") %
                        {'volunteer': volunteer})
        return self.cleaned_data.get(template)


class UsersWidget(ModelSelect2MultipleWidget):
    model = User
    search_fields = [ '%s__icontains' % field for field in UserAdmin.search_fields ]


class ConferenceForm(forms.ModelForm):
    class Meta:
        model = Conference
        fields = [
            'name', 'venue', 'city', 'contact_email', 'acceptances_disclosure_date',
            'schedule_publishing_date', 'schedule_redirection_url',
            'volunteers_opening_date', 'volunteers_closing_date',
            'end_date', 'video_publishing_date',
            'reply_email', 'secure_domain', 'staff',
        ]
        widgets = {
            'staff': UsersWidget(),
        }
        help_texts = {
            'staff': _('New staff members will be informed of their new position by e-mail.'),
        }


class HomepageForm(forms.ModelForm):
    class Meta:
        model = Conference
        fields = ['home']


class CreateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean(self):
        super().clean()
        user = User(first_name=self.cleaned_data.get('first_name'), last_name=self.cleaned_data.get('last_name'))
        username = slugify(user.get_full_name())
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_('An user with that firstname and that lastname already exists.'))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('A user with that email already exists.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = slugify(user.get_full_name())
        user.set_password(get_random_string(length=32))
        if commit:
            user.save()
        return user


class TrackForm(OnSiteNamedModelForm):
    class Meta:
        model = Track
        fields = ['name', 'description']


class TalkCategoryForm(OnSiteNamedModelForm):
    class Meta:
        model = TalkCategory
        fields = ['name', 'duration', 'color', 'label', 'opening_date', 'closing_date']


class RoomForm(OnSiteNamedModelForm):
    class Meta:
        model = Room
        fields = ['name', 'label', 'capacity']


class TagForm(OnSiteNamedModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'color', 'inverted', 'public', 'staff']


class ActivityForm(OnSiteNamedModelForm):
    class Meta:
        model = Activity
        fields = ['name', 'description']


class VolunteerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.conference = kwargs.pop('conference')
        super().__init__(*args, **kwargs)
        activities = Activity.objects.filter(site=self.conference.site)
        if activities.exists():
            self.fields['activities'].queryset = activities
        else:
            del self.fields['activities']

    # we should manually check (site, email) uniqueness as the site is not part of the form
    def clean_email(self):
        email = self.cleaned_data['email']
        if (not self.instance or self.instance.email != email) \
                and self._meta.model.objects.filter(site=self.conference.site, email=email).exists():
            raise self.instance.unique_error_message(self._meta.model, ['email'])
        return email

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.site = self.conference.site
        if commit:
            obj.save()
        return obj

    class Meta:
        model = Volunteer
        fields = ['name', 'email', 'phone_number', 'sms_prefered', 'activities', 'notes']
        widgets = {
            'activities': forms.CheckboxSelectMultiple,
        }


def get_talk_speaker_form_class(site):
    fields = ['name', 'email', 'twitter', 'linkedin', 'github', 'website', 'facebook', 'mastodon', 'phone_number']
    widget = ModelSelect2MultipleWidget(model=Participant, queryset=Participant.objects.filter(site=site),
                                        search_fields=['%s__icontains' % field for field in fields])
    return modelform_factory(Talk, form=TalkStaffForm, widgets={'speakers': widget})
