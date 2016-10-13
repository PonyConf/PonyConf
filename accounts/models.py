from enum import IntEnum

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from ponyconf.utils import PonyConfModel, enum_to_choices

from .utils import generate_user_uid


class Profile(PonyConfModel):

    user = models.OneToOneField(User)
    biography = models.TextField(blank=True, verbose_name=_('Biography'))
    email_token = models.CharField(max_length=12, default=generate_user_uid, unique=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_absolute_url(self):
        return reverse('profile')


class Option(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return ugettext(self.name)


class Transport(Option):
    pass


class Connector(Option):
    pass


class Participation(PonyConfModel):

    LICENCES = IntEnum('Video licence', 'CC-Zero CC-BY CC-BY-SA CC-BY-ND CC-BY-NC CC-BY-NC-SA CC-BY-NC-ND')
    ACCOMMODATION_NO = 0
    ACCOMMODATION_HOTEL = 1
    ACCOMMODATION_HOMESTAY = 2
    ACCOMMODATION_CHOICES = (
        (ACCOMMODATION_NO, _('No')),
        (ACCOMMODATION_HOTEL, _('Hotel')),
        (ACCOMMODATION_HOMESTAY, _('Homestay')),
    )

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    user = models.ForeignKey(User)


    need_transport = models.NullBooleanField(verbose_name=_('Defray transportation?'), default=None)
    arrival = models.DateTimeField(blank=True, null=True)
    departure = models.DateTimeField(blank=True, null=True)
    transport = models.ManyToManyField(Transport, verbose_name=_("I want to travel by"), blank=True)
    transport_city_outward = models.CharField(blank=True, default='', max_length=256, verbose_name=_("Departure city"))
    transport_city_return = models.CharField(blank=True, default='', max_length=256, verbose_name=_("Return city"), help_text=_("If different from departure city"))
    transport_booked = models.BooleanField(default=False)

    accommodation = models.IntegerField(choices=ACCOMMODATION_CHOICES, verbose_name=_('Need accommodation?'), null=True, blank=True)
    accommodation_booked = models.BooleanField(default=False)

    constraints = models.TextField(blank=True, verbose_name=_("Constraints"))
    connector = models.ManyToManyField(Connector, verbose_name=_("I can output"), blank=True)
    sound = models.BooleanField(_("I need sound"), default=False)

    videotaped = models.BooleanField(_("I'm ok to be recorded on video"), default=True)
    video_licence = models.IntegerField(choices=enum_to_choices(LICENCES), default=2, verbose_name=_("Video licence"))

    notes = models.TextField(default='', blank=True, verbose_name=_("Notes"), help_text=_('This field is only visible by organizers.'))
    orga = models.BooleanField(default=False)

    class Meta:
        # A User can participe only once to a Conference (= Site)
        unique_together = ('site', 'user')

    def __str__(self):
        return str(self.user.profile)

    def get_absolute_url(self):
        return reverse('show-speaker', kwargs={'username': self.user.username})

    def is_orga(self):
        return self.orga

    def is_staff(self):
        return self.is_orga() or self.topic_set.exists() or self.track_set.exists()

    @property
    def topic_set(self):
        return self.user.topic_set.filter(site=self.site)

    @property
    def track_set(self):
        return self.user.track_set.filter(site=self.site)

    @property
    def talk_set(self):
        return self.user.talk_set.filter(site=self.site)

    # return True, False or None if availabilities have not been filled
    def is_available(self, start, end=None):
        if not self.availabilities.exists():
            return None
        for timeslot in self.availabilities.all():
            if start < timeslot.start:
                continue
            if start > timeslot.end:
                continue
            if end:
                assert(start < end)
                if end > timeslot.end:
                    continue
            return True
        return False


class AvailabilityTimeslot(models.Model):

    participation = models.ForeignKey(Participation, related_name='availabilities')
    start = models.DateTimeField(blank=True)
    end = models.DateTimeField(blank=True)
