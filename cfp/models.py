
import uuid

from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.utils import timezone

from ponyconf.utils import PonyConfModel

from autoslug import AutoSlugField
from colorful.fields import RGBColorField

from .utils import query_sum

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext


#from ponyconf.utils import PonyConfModel, enum_to_choices



class Conference(models.Model):

    site = models.OneToOneField(Site, on_delete=models.CASCADE)
    name = models.CharField(blank=True, max_length=100)
    home = models.TextField(blank=True, default="")
    venue = models.TextField(blank=True, default="")
    city = models.CharField(max_length=64, blank=True, default="")
    contact_email = models.CharField(max_length=100, blank=True)
    #subscriptions_open = models.BooleanField(default=False) # workshop subscription

    #def cfp_is_open(self):
    #    events = Event.objects.filter(site=self.site)
    #    return any(map(lambda x: x.is_open(), events))

    #@property
    #def opened_events(self):
    #    now = timezone.now()
    #    return Event.objects.filter(site=self.site)\
    #                        .filter(Q(opening_date__isnull=True) | Q(opening_date__lte=now))\
    #                        .filter(Q(closing_date__isnull=True) | Q(closing_date__gte=now))

    def from_email(self):
        return self.name+' <'+self.contact_email+'>'

    def __str__(self):
        return str(self.site)


class Participant(PonyConfModel):

    #LICENCES = IntEnum('Video licence', 'CC-Zero CC-BY CC-BY-SA CC-BY-ND CC-BY-NC CC-BY-NC-SA CC-BY-NC-ND')

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    name = models.CharField(max_length=128, blank=True)
    email = models.EmailField()

    phone_number = models.CharField(max_length=16, blank=True, default='', verbose_name=_('Phone number'))
    biography = models.TextField(blank=True, verbose_name=_('Biography'))
    token = models.UUIDField(default=uuid.uuid4, editable=False)

    # TALK
    #videotaped = models.BooleanField(_("I'm ok to be recorded on video"), default=True)
    #video_licence = models.IntegerField(choices=enum_to_choices(LICENCES), default=2, verbose_name=_("Video licence"))
    #sound = models.BooleanField(_("I need sound"), default=False)

    notes = models.TextField(default='', blank=True, verbose_name=_("Notes"), help_text=_('This field is only visible by organizers.'))
    vip = models.BooleanField(default=False)

    class Meta:
        # A User can participe only once to a Conference (= Site)
        unique_together = ('site', 'email')

    def __str__(self):
        return str(self.name)

    #def get_absolute_url(self):
    #    return reverse('show-participant', kwargs={'username': self.user.username})

    #def is_orga(self):
    #    return self.orga

    #def is_staff(self):
    #    return self.is_orga() or self.topic_set.exists() or self.track_set.exists()

    #@property
    #def topic_set(self):
    #    return self.user.topic_set.filter(site=self.site)

    #@property
    #def track_set(self):
    #    return self.user.track_set.filter(site=self.site)

    #@property
    #def talk_set(self):
    #    return self.user.talk_set.filter(site=self.site)

    #@property
    #def accepted_talk_set(self):
    #    return self.talk_set.filter(accepted=True)
    #@property
    #def pending_talk_set(self):
    #    return self.talk_set.filter(accepted=None)
    #@property
    #def refused_talk_set(self):
    #    return self.talk_set.filter(accepted=False)
    #@property
    #def not_refused_talk_set(self): # accepted + pending
    #    return self.talk_set.exclude(accepted=False)


class Track(PonyConfModel):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    name = models.CharField(max_length=128, verbose_name=_('Name'))
    slug = AutoSlugField(populate_from='name')
    description = models.TextField(blank=True, verbose_name=_('Description'))

    #managers = models.ManyToManyField(User, blank=True, verbose_name=_('Managers'))

    class Meta:
        unique_together = ('site', 'name')

    #def estimated_duration(self):
    #    return sum([talk.estimated_duration for talk in self.talk_set.all()])

    def __str__(self):
        return self.name

    #def get_absolute_url(self):
    #    return reverse('list-talks') + '?track=%s' % self.slug


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

    #def get_absolute_url(self):
    #    return reverse('list-talks') + '?kind=%d' % self.pk


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

    #proposer = models.ForeignKey(User, related_name='+')
    speakers = models.ManyToManyField(Participant, verbose_name=_('Speakers'))
    title = models.CharField(max_length=128, verbose_name=_('Talk Title'))
    slug = AutoSlugField(populate_from='title', unique=True)
    #abstract = models.CharField(max_length=255, blank=True, verbose_name=_('Abstract'))
    description = models.TextField(blank=True, verbose_name=_('Description of your talk'))
    track = models.ForeignKey(Track, blank=True, null=True, verbose_name=_('Track'))
    notes = models.TextField(blank=True, verbose_name=_('Message to organizers'), help_text=_('If you have any constraint or if you have anything that may help you to select your talk, like a video or slides of your talk, please write it down here'))
    category = models.ForeignKey(TalkCategory, blank=True, null=True, verbose_name=_('Talk Category'))
    videotaped = models.BooleanField(_("I'm ok to be recorded on video"), default=True)
    video_licence = models.CharField(choices=LICENCES, default='CC-BY-SA', max_length=10, verbose_name=_("Video licence"))
    sound = models.BooleanField(_("I need sound"), default=False)
    accepted = models.NullBooleanField(default=None)
    #start_date = models.DateTimeField(null=True, blank=True, default=None)
    duration = models.PositiveIntegerField(default=0, verbose_name=_('Duration (min)'))
    #room = models.ForeignKey(Room, blank=True, null=True, default=None)
    plenary = models.BooleanField(default=False)
    #materials = models.FileField(null=True, upload_to=talk_materials_destination, verbose_name=_('Materials'),
    #                             help_text=_('You can use this field to share some materials related to your intervention.'))

    token = models.UUIDField(default=uuid.uuid4, editable=False)


    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title

    def get_speakers_str(self):
        speakers = [str(Participant.objects.get(site=self.site, user=speaker)) for speaker in self.speakers.all()]
        if len(speakers) == 0:
            return 'superman'
        elif len(speakers) == 1:
            return speakers[0]
        else:
            return ', '.join(speakers[:-1]) + ' & ' + str(speakers[-1])

    @property
    def estimated_duration(self):
        return self.duration or self.category.duration

    #def get_absolute_url(self):
    #    return reverse('show-talk', kwargs={'slug': self.slug})

    def score(self):
        if self.vote_set.exists():
            return query_sum(self.vote_set, 'vote') / len(self.vote_set.all())
        else:
            return 0

    @property
    def end_date(self):
        if self.estimated_duration:
            return self.start_date + timedelta(minutes=self.estimated_duration)
        else:
            return None

    #@property
    #def dtstart(self):
    #    return self.start_date.strftime('%Y%m%dT%H%M%SZ')

    #@property
    #def dtend(self):
    #    return self.end_date.strftime('%Y%m%dT%H%M%SZ')

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

    #def get_absolute_url(self):
    #    return self.talk.get_absolute_url()
