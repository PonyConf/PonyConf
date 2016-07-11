from enum import IntEnum

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models

from ponyconf.utils import PonyConfModel, enum_to_choices

from .utils import generate_user_uid


class Profile(PonyConfModel):

    user = models.OneToOneField(User)
    biography = models.TextField(blank=True, verbose_name='Biography')
    email_token = models.CharField(max_length=12, default=generate_user_uid, unique=True)
    notes = models.TextField(default='')

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def get_absolute_url(self):
        return reverse('profile')


class Option(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Transport(Option):
    pass


class Connector(Option):
    pass


class Participation(PonyConfModel):

    LICENCES = IntEnum('Video licence', 'CC-Zero CC-BY CC-BY-SA CC-BY-ND CC-BY-NC CC-BY-NC-SA CC-BY-NC-ND')

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    user = models.ForeignKey(User)

    arrival = models.DateTimeField(blank=True, null=True)
    departure = models.DateTimeField(blank=True, null=True)
    transport = models.ManyToManyField(Transport, verbose_name="I'm ok to travel by", blank=True)
    connector = models.ManyToManyField(Connector, verbose_name="I can output", blank=True)
    constraints = models.TextField(blank=True)
    sound = models.BooleanField("I need sound", default=False)
    videotaped = models.BooleanField("I'm ok to be recorded on video", default=True)
    video_licence = models.IntegerField(choices=enum_to_choices(LICENCES), default=1)
    orga = models.BooleanField(default=False)

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

    @property
    def topic_set(self):
        from proposals.models import Topic
        return Topic.objects.filter(site=self.site, reviewers=self.user)
