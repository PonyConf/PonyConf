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

from autoslug import AutoSlugField
from colorful.fields import RGBColorField

import uuid
from datetime import timedelta

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
    schedule_publishing_date = models.DateTimeField(null=True, blank=True, default=None, verbose_name=_('Schedule publishing date'))

    custom_css = models.TextField(blank=True)
    external_css_link = models.URLField(blank=True)

    #subscriptions_open = models.BooleanField(default=False) # workshop subscription

    #def cfp_is_open(self):
    #    events = Event.objects.filter(site=self.site)
    #    return any(map(lambda x: x.is_open(), events))

    @property
    def opened_categories(self):
        now = timezone.now()
        return TalkCategory.objects.filter(site=self.site)\
                            .filter(Q(opening_date__isnull=True) | Q(opening_date__lte=now))\
                            .filter(Q(closing_date__isnull=True) | Q(closing_date__gte=now))

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

    name = models.CharField(max_length=128, verbose_name=_('Your Name'))
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

    notes = models.TextField(default='', blank=True, verbose_name=_("Notes"), help_text=_('This field is only visible by organizers.'))

    vip = models.BooleanField(default=False)

    conversation = models.OneToOneField(MessageThread)

    objects = ParticipantManager()

    def get_absolute_url(self):
        return reverse('participant-details', kwargs={'participant_id': self.token})

    class Meta:
        # A User can participe only once to a Conference (= Site)
        unique_together = ('site', 'email')

    def __str__(self):
        return str(self.name)

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

    def estimated_duration(self):
        return sum([talk.estimated_duration for talk in self.talk_set.all()])

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('talk-list') + '?track=%s' % self.slug


class Room(models.Model):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    slug = AutoSlugField(populate_from='name')
    name = models.CharField(max_length=256, blank=True, default="")
    label = models.CharField(max_length=256, blank=True, default="")
    capacity = models.IntegerField(default=0)

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


#def talk_materials_destination(talk, filename):
#    return join(talk.site.name, talk.slug, filename)


class TalkManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(score=Coalesce(Avg('vote__vote'), 0))
        return qs


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
    #abstract = models.CharField(max_length=255, blank=True, verbose_name=_('Abstract'))
    description = models.TextField(verbose_name=_('Description of your talk'))
    track = models.ForeignKey(Track, blank=True, null=True, verbose_name=_('Track'))
    notes = models.TextField(blank=True, verbose_name=_('Message to organizers'), help_text=_('If you have any constraint or if you have anything that may help you to select your talk, like a video or slides of your talk, please write it down here'))
    category = models.ForeignKey(TalkCategory, verbose_name=_('Talk Category'))
    videotaped = models.BooleanField(_("I'm ok to be recorded on video"), default=True)
    video_licence = models.CharField(choices=LICENCES, default='CC-BY-SA', max_length=10, verbose_name=_("Video licence"))
    sound = models.BooleanField(_("I need sound"), default=False)
    accepted = models.NullBooleanField(default=None)
    start_date = models.DateTimeField(null=True, blank=True, default=None, verbose_name=_('Beginning date and time'))
    duration = models.PositiveIntegerField(default=0, verbose_name=_('Duration (min)'))
    room = models.ForeignKey(Room, blank=True, null=True, default=None)
    plenary = models.BooleanField(default=False)
    #materials = models.FileField(null=True, upload_to=talk_materials_destination, verbose_name=_('Materials'),
    #                             help_text=_('You can use this field to share some materials related to your intervention.'))

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

    #@property
    #def materials_name(self):
    #    return basename(self.materials.name)

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
