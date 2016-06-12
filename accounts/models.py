from enum import IntEnum

from django.contrib.auth.models import User
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models

__all__ = ['Profile', 'Speaker']


def enum_to_choices(enum):
    return ((item.value, item.name) for item in list(enum))


class Profile(models.Model):

    user = models.OneToOneField(User)
    biography = models.TextField(blank=True, verbose_name='Biography')

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_absolute_url(self):
        return reverse('profile')


class Speaker(models.Model):

    TRANSPORTS = IntEnum('Transport', 'train plane')
    CONNECTORS = IntEnum('Connector', 'VGA HDMI miniDP')

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    user = models.ForeignKey(User)
    arrival = models.DateTimeField(blank=True, null=True)
    departure = models.DateTimeField(blank=True, null=True)
    transport = models.IntegerField(choices=enum_to_choices(TRANSPORTS), blank=True, null=True)
    connector = models.IntegerField(choices=enum_to_choices(CONNECTORS), blank=True, null=True)
    constraints = models.TextField()

    objects = models.Manager()
    on_site = CurrentSiteManager()

    class Meta:
        unique_together = ('site', 'user')

    def __str__(self):
        return str(self.user.profile)

    def get_absolute_url(self):
        return reverse('show-speaker', kwargs={'username': self.user.username})


def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

models.signals.post_save.connect(create_profile, sender=User, weak=False, dispatch_uid='create_profile')
