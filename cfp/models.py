from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Count, Avg, Case, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.html import escape, format_html

from autoslug import AutoSlugField
from colorful.fields import RGBColorField
from functools import partial

import uuid
from datetime import timedelta
from os.path import join, basename

from ponyconf.utils import PonyConfModel
from mailing.models import MessageThread



class Conference(models.Model):
    site = models.OneToOneField(Site, on_delete=models.CASCADE)

    name = models.CharField(blank=True, max_length=100, verbose_name=_('Conference name'))
    home = models.TextField(blank=True, default="", verbose_name=_('Homepage (markdown)'))
    venue = models.TextField(blank=True, default="", verbose_name=_('Venue information'))
    city = models.CharField(max_length=64, blank=True, default="", verbose_name=_('City'))
    contact_email = models.CharField(max_length=100, blank=True, verbose_name=_('Contact email'))
    reply_email = models.CharField(max_length=100, blank=True, verbose_name=_('Reply email'))
    staff = models.ManyToManyField(User, blank=True, verbose_name=_('Staff members'))
    secure_domain = models.BooleanField(default=True, verbose_name=_('Secure domain (HTTPS)'))
    acceptances_disclosure_date = models.DateTimeField(null=True, blank=True, default=None, verbose_name=_('Acceptances disclosure date'))
    schedule_publishing_date = models.DateTimeField(null=True, blank=True, default=None, verbose_name=_('Schedule publishing date'))
    schedule_redirection_url = models.URLField(blank=True, default='', verbose_name=_('Schedule redirection URL'),
                                               help_text=_('If specified, schedule tab will redirect to this URL.'))
    volunteers_opening_date = models.DateTimeField(null=True, blank=True, default=None, verbose_name=_('Volunteers enrollment opening date'))
    volunteers_closing_date = models.DateTimeField(null=True, blank=True, default=None, verbose_name=_('Volunteers enrollment closing date'))

    custom_css = models.TextField(blank=True)
    external_css_link = models.URLField(blank=True)

    def volunteers_enrollment_is_open(self):
        now = timezone.now()
        opening = self.volunteers_opening_date
        closing = self.volunteers_closing_date
        return opening and opening < now and (not closing or closing > now)

    @property
    def opened_categories(self):
        now = timezone.now()
        return TalkCategory.objects.filter(site=self.site)\
                            .filter(Q(opening_date__isnull=True) | Q(opening_date__lte=now))\
                            .filter(Q(closing_date__isnull=True) | Q(closing_date__gte=now))

    @property
    def disclosed_acceptances(self):
        # acceptances are automatically disclosed if the schedule is published
        return (self.acceptances_disclosure_date and self.acceptances_disclosure_date <= timezone.now()) or self.schedule_available

    @property
    def schedule_available(self):
        return self.schedule_publishing_date and self.schedule_publishing_date <= timezone.now()

    def from_email(self):
        return self.name+' <'+self.contact_email+'>'

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)
        if self.reply_email is not None:
            try:
                self.reply_email.format(token='a' * 80)
            except Exception:
                raise ValidationError({
                    'reply_email': _('The reply email should be a formatable string accepting a token argument (e.g. ponyconf+{token}@exemple.com).'),
                })

    def __str__(self):
        return str(self.site)


class ParticipantManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(
            accepted_talk_count=Count(Case(When(talk__accepted=True, then='talk__pk'), output_field=models.IntegerField()), distinct=True),
            pending_talk_count=Count(Case(When(talk__accepted=None, then='talk__pk'), output_field=models.IntegerField()), distinct=True),
            refused_talk_count=Count(Case(When(talk__accepted=False, then='talk__pk'), output_field=models.IntegerField()), distinct=True),
        )
        return qs


class Participant(PonyConfModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, verbose_name=_('Name'))
    email = models.EmailField()
    biography = models.TextField(verbose_name=_('Biography'))
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    twitter = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Twitter'))
    linkedin = models.CharField(max_length=100, blank=True, default='', verbose_name=_('LinkedIn'))
    github = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Github'))
    website = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Website'))
    facebook = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Facebook'))
    mastodon = models.CharField(max_length=100, blank=True, default='', verbose_name=_('Mastodon'))
    phone_number = models.CharField(max_length=64, blank=True, default='', verbose_name=_('Phone number'))
    language = models.CharField(max_length=10, blank=True)
    notes = models.TextField(default='', blank=True, verbose_name=_("Notes"),
                             help_text=_('This field is only visible by organizers.'))
    vip = models.BooleanField(default=False, verbose_name=_('Invited speaker'))
    conversation = models.OneToOneField(MessageThread)

    objects = ParticipantManager()

    def get_absolute_url(self):
        return reverse('participant-details', kwargs=dict(participant_id=self.token))

    def get_secret_url(self, full=False):
        url = reverse('proposal-dashboard', kwargs={'speaker_token': self.token})
        if full:
            url = ('https' if self.site.conference.secure_domain else 'http') + '://' + self.site.domain + url
        return url

    def get_csv_row(self):
        return map(partial(getattr, self), ['pk', 'name', 'email', 'biography', 'twitter', 'linkedin', 'github', 'website', 'facebook', 'mastodon', 'phone_number', 'notes'])

    class Meta:
        # A User can participe only once to a Conference (= Site)
        unique_together = ('site', 'name')
        unique_together = ('site', 'email')

    def __str__(self):
        return str(self.name)

    @property
    def co_speaker_set(self):
        return Participant.objects.filter(site=self.site, talk__in=self.talk_set.values_list('pk')).exclude(pk=self.pk).order_by('name').distinct()

    @property
    def accepted_talk_set(self):
        return self.talk_set.filter(accepted=True)
    @property
    def pending_talk_set(self):
        return self.talk_set.filter(accepted=None)
    @property
    def refused_talk_set(self):
        return self.talk_set.filter(accepted=False)


class Track(PonyConfModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, verbose_name=_('Name'))
    slug = AutoSlugField(populate_from='name')
    description = models.TextField(blank=True, verbose_name=_('Description'))

    #managers = models.ManyToManyField(User, blank=True, verbose_name=_('Managers'))

    class Meta:
        unique_together = ('site', 'name')
        ordering = ['name']

    def estimated_duration(self):
        return sum([talk.estimated_duration for talk in self.talk_set.all()])

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('talk-list') + '?track=%s' % self.slug


class Room(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    name = models.CharField(max_length=256, blank=True, default='', verbose_name=_('Name'))
    slug = AutoSlugField(populate_from='name')
    label = models.CharField(max_length=256, blank=True, default='', verbose_name=_('Label'))
    capacity = models.IntegerField(default=0, verbose_name=_('Capacity'))

    class Meta:
        unique_together = ['site', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('room-details', kwargs={'slug': self.slug})

    @property
    def talks(self):
        return self.talk_set.exclude(accepted=False)

    @property
    def talks_by_date(self):
        return self.talks.filter(start_date__isnull=False).exclude(duration=0, category__duration=0).order_by('start_date').all()

    @property
    def unscheduled_talks(self):
        return self.talks.filter(Q(start_date__isnull=True) | Q(duration=0, category__duration=0)).all()


class Tag(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    name = models.CharField(max_length=256, verbose_name=_('Name'))
    slug = AutoSlugField(populate_from='name')
    color = RGBColorField(default='#ffffff', verbose_name=_("Color"))
    inverted = models.BooleanField(default=False)
    public = models.BooleanField(default=False, verbose_name=_('Show the tag on the public program'))
    staff = models.BooleanField(default=False, verbose_name=_('Show the tag on the staff program'))

    def get_absolute_url(self):
        return reverse('tag-list')

    def get_filter_url(self):
        return reverse('talk-list') + '?tag=' + self.slug

    @property
    def link(self):
        return format_html('<a href="{url}">{content}</a>', **{
            'url': self.get_filter_url(),
            'content': self.label,
        })

    @property
    def label(self):
        return format_html('<span class="label" style="{style}">{name}</span>', **{
            'style': self.style,
            'name': self.name,
        })

    @property
    def style(self):
        return mark_safe('background-color: {bg}; color: {fg}; vertical-align: middle;'.format(**{
            'fg': '#fff' if self.inverted else '#000',
            'bg': self.color,
        }))

    def __str__(self):
        return self.name


class TalkCategory(models.Model): # type of talk (conf 30min, 1h, stand, …)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    duration = models.PositiveIntegerField(default=0, verbose_name=_('Default duration (min)'))
    color = RGBColorField(default='#ffffff', verbose_name=_("Color on program"))
    label = models.CharField(max_length=64, verbose_name=_("Label on program"), blank=True, default="")
    opening_date = models.DateTimeField(null=True, blank=True, default=None)
    closing_date = models.DateTimeField(null=True, blank=True, default=None)

    def is_open(self):
        now = timezone.now()
        if self.opening_date and now < self.opening_date:
            return False
        if self.closing_date and now > self.closing_date:
            return False
        return True

    class Meta:
        unique_together = ('site', 'name')
        ordering = ('pk',)
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self):
        return ugettext(self.name)

    def get_absolute_url(self):
        return reverse('category-list')

    def get_filter_url(self):
        return reverse('talk-list') + '?category=%d' % self.pk


#class Attendee(PonyConfModel):
#
#    user = models.ForeignKey(User, null=True)
#    name = models.CharField(max_length=64, blank=True, default="")
#    email = models.EmailField(blank=True, default="")
#
#    def get_name(self):
#        if self.user:
#            return str(self.user.profile)
#        else:
#            return self.name
#    get_name.short_description = _('Name')
#
#    def get_email(self):
#        if self.user:
#            return self.user.email
#        else:
#            return self.email
#    get_email.short_description = _('Email')
#
#    def __str__(self):
#        return self.get_name()


class TalkManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(score=Coalesce(Avg('vote__vote'), 0))
        return qs


def talks_materials_destination(talk, filename):
    return join(talk.site.name, talk.slug, filename)


class Talk(PonyConfModel):
    LICENCES = (
        ('CC-Zero CC-BY', 'CC-Zero CC-BY'),
        ('CC-BY-SA', 'CC-BY-SA'),
        ('CC-BY-ND', 'CC-BY-ND'),
        ('CC-BY-NC', 'CC-BY-NC'),
        ('CC-BY-NC-SA','CC-BY-NC-SA'),
        ('CC-BY-NC-ND', 'CC-BY-NC-ND'),
    )

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    speakers = models.ManyToManyField(Participant, verbose_name=_('Speakers'))
    title = models.CharField(max_length=128, verbose_name=_('Talk Title'))
    slug = AutoSlugField(populate_from='title', unique=True)
    description = models.TextField(verbose_name=_('Description of your talk'),
                                   help_text=_('This description will be visible on the program.'))
    track = models.ForeignKey(Track, blank=True, null=True, verbose_name=_('Track'))
    tags = models.ManyToManyField(Tag, blank=True)
    notes = models.TextField(blank=True, verbose_name=_('Message to organizers'),
                                   help_text=_('If you have any constraint or if you have anything that may '
                                               'help you to select your talk, like a video or slides of your'
                                               ' talk, please write it down here. This field will only be '
                                               'visible by organizers.'))
    category = models.ForeignKey(TalkCategory, verbose_name=_('Talk Category'))
    videotaped = models.BooleanField(_("I'm ok to be recorded on video"), default=True)
    video_licence = models.CharField(choices=LICENCES, default='CC-BY-SA',
                                     max_length=10, verbose_name=_("Video licence"))
    sound = models.BooleanField(_("I need sound"), default=False)
    accepted = models.NullBooleanField(default=None)
    confirmed = models.NullBooleanField(default=None)
    start_date = models.DateTimeField(null=True, blank=True, default=None, verbose_name=_('Beginning date and time'))
    duration = models.PositiveIntegerField(default=0, verbose_name=_('Duration (min)'))
    room = models.ForeignKey(Room, blank=True, null=True, default=None)
    plenary = models.BooleanField(default=False)
    materials = models.FileField(null=True, blank=True, upload_to=talks_materials_destination, verbose_name=_('Materials'),
                                     help_text=_('You can use this field to share some materials related to your intervention.'))
    video = models.URLField(max_length=1000, blank=True, default='', verbose_name='Video URL')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    conversation = models.OneToOneField(MessageThread)

    objects = TalkManager()

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title

    def get_speakers_str(self):
        speakers = list(map(str, self.speakers.all()))
        if len(speakers) == 0:
            return 'superman'
        elif len(speakers) == 1:
            return speakers[0]
        else:
            return ', '.join(speakers[:-1]) + ' & ' + str(speakers[-1])

    def get_status_str(self):
        if self.accepted is True:
            if self.confirmed is True:
                return _('Confirmed')
            elif self.confirmed is False:
                return _('Cancelled')
            else:
                return _('Waiting confirmation')
        elif self.accepted is False:
            return _('Refused')
        else:
            return _('Pending decision, score: %(score).1f') % {'score': self.score}

    def get_status_color(self):
        if self.accepted is True:
            if self.confirmed is True:
                return 'success'
            elif self.confirmed is False:
                return 'danger'
            else:
                return 'info'
        elif self.accepted is False:
            return 'default'
        else:
            return 'warning'

    def get_tags_html(self):
        return mark_safe(' '.join(map(lambda tag: tag.link, self.tags.all())))

    def get_csv_row(self):
        return [
            self.pk,
            self.title,
            self.description,
            self.category,
            self.track,
            [speaker.pk for speaker in self.speakers.all()],
            [speaker.name for speaker in self.speakers.all()],
            [tag.name for tag in self.tags.all()],
            1 if self.videotaped else 0,
            self.video_licence,
            1 if self.sound else 0,
            self.estimated_duration,
            self.room,
            1 if self.plenary else 0,
            self.materials,
            self.video,
        ]

    @property
    def estimated_duration(self):
        return self.duration or self.category.duration

    def get_absolute_url(self):
        return reverse('talk-details', kwargs={'talk_id': self.token})

    @property
    def end_date(self):
        if self.estimated_duration:
            return self.start_date + timedelta(minutes=self.estimated_duration)
        else:
            return None

    @property
    def materials_name(self):
        return basename(self.materials.name)

    class Meta:
        ordering = ('category__id', 'title',)


class Vote(PonyConfModel):
    talk = models.ForeignKey(Talk)
    user = models.ForeignKey(User)
    vote = models.IntegerField(validators=[MinValueValidator(-2), MaxValueValidator(2)], default=0)

    class Meta:
        unique_together = ('talk', 'user')

    def __str__(self):
        return "%+i by %s for %s" % (self.vote, self.user, self.talk)

    def get_absolute_url(self):
        return self.talk.get_absolute_url()


class Volunteer(PonyConfModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, verbose_name=_('Your Name'))
    email = models.EmailField(verbose_name=_('Email'))
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    phone_number = models.CharField(max_length=64, blank=True, default='', verbose_name=_('Phone number'))
    sms_prefered = models.BooleanField(default=False, verbose_name=_('SMS prefered'))
    language = models.CharField(max_length=10, blank=True)
    notes = models.TextField(default='', blank=True, verbose_name=_('Notes'),
                             help_text=_('If you have some constraints, you can indicate them here.'))
    conversation = models.OneToOneField(MessageThread)

    def get_absolute_url(self):
        return reverse('volunteer-details', kwargs=dict(volunteer_id=self.pk))

    def get_secret_url(self, full=False):
        url = reverse('volunteer-home', kwargs=dict(volunteer_token=self.token))
        if full:
            url = ('https' if self.site.conference.secure_domain else 'http') + '://' + self.site.domain + url
        return url

    def get_csv_row(self):
        return [
            self.pk,
            self.name,
            self.email,
            self.phone_number,
            1 if self.sms_prefered else 0,
            self.notes,
        ]

    class Meta:
        # A volunteer can participe only once to a Conference (= Site)
        unique_together = ('site', 'email')

    def __str__(self):
        return str(self.name)


class Activity(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    name = models.CharField(max_length=256, verbose_name=_('Name'))
    slug = AutoSlugField(populate_from='name')
    description = models.TextField(blank=True, verbose_name=_('Description'))
    volunteers = models.ManyToManyField(Volunteer, blank=True, related_name='activities', verbose_name=_('Volunteer'))

    class Meta:
        unique_together = ('site', 'name')
        verbose_name = _('Activity')
        verbose_name_plural = _('Activities')

    def get_absolute_url(self):
        return reverse('activity-list')

    def get_filter_url(self):
        return reverse('volunteer-list') + '?activity=' + self.slug

    def __str__(self):
        return self.name
