from enum import IntEnum

from django.contrib.auth.models import User
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models

from ponyconf.utils import PonyConfModel, enum_to_choices

from .utils import generate_user_uid

__all__ = ['Profile']


class Profile(PonyConfModel):

    user = models.OneToOneField(User)
    biography = models.TextField(blank=True, verbose_name='Biography')
    email_token = models.CharField(max_length=12, default=generate_user_uid, unique=True)
    notes = models.TextField(default='')

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_absolute_url(self):
        return reverse('profile')


class Participation(PonyConfModel):

    TRANSPORTS = IntEnum('Transport', 'train plane others')
    CONNECTORS = IntEnum('Connector', 'VGA HDMI miniDP')

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    user = models.ForeignKey(User)

    arrival = models.DateTimeField(blank=True, null=True)
    departure = models.DateTimeField(blank=True, null=True)
    # TODO: These should multi-choice fields
    transport = models.IntegerField(choices=enum_to_choices(TRANSPORTS), blank=True, null=True)
    connector = models.IntegerField(choices=enum_to_choices(CONNECTORS), blank=True, null=True)
    constraints = models.TextField(blank=True)
    sound = models.BooleanField("I need sound", default=False)
    orga = models.BooleanField(default=False)

    objects = models.Manager()
    on_site = CurrentSiteManager()

    class Meta:
        # A User can participe only once to a Conference (= Site)
        unique_together = ('site', 'user')

    def __str__(self):
        return str(self.user.profile)

    def get_absolute_url(self):
        return reverse('show-speaker', kwargs={'username': self.user.username})

    def is_orga(self):
        return self.user.is_superuser or self.orga

    def is_staff(self):
        return self.is_orga() or self.topic_set.exists()
