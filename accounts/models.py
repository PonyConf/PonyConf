from enum import IntEnum

from django.contrib.auth.models import User
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models

from .utils import enum_to_choices, generate_user_uid
from proposals.models import Topic


__all__ = ['Profile']


class Profile(models.Model):

    user = models.OneToOneField(User)
    biography = models.TextField(blank=True, verbose_name='Biography')
    email_token = models.CharField(max_length=12, default=generate_user_uid)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_absolute_url(self):
        return reverse('profile')


class Participation(models.Model):

    TRANSPORTS = IntEnum('Transport', 'train plane')
    CONNECTORS = IntEnum('Connector', 'VGA HDMI miniDP')

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    user = models.ForeignKey(User)

    arrival = models.DateTimeField(blank=True, null=True)
    departure = models.DateTimeField(blank=True, null=True)
    # TODO: These should multi-choice fields
    transport = models.IntegerField(choices=enum_to_choices(TRANSPORTS), blank=True, null=True)
    connector = models.IntegerField(choices=enum_to_choices(CONNECTORS), blank=True, null=True)
    constraints = models.TextField(blank=True)

    # Participe as reviewer for theses topics
    review_topics = models.ManyToManyField(Topic, blank=True)

    objects = models.Manager()
    on_site = CurrentSiteManager()

    class Meta:
        # A User can participe only once to a Conference (= Site)
        unique_together = ('site', 'user')

    def __str__(self):
        return "%s participation to %s" % (str(self.user.profile), self.site.name)

    def get_absolute_url(self):
        return reverse('show-participation', kwargs={'username': self.user.username})


def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

models.signals.post_save.connect(create_profile, sender=User, weak=False, dispatch_uid='create_profile')
