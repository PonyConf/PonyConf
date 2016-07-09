from enum import IntEnum

from django.contrib.auth.models import User
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from autoslug import AutoSlugField
from sortedm2m.fields import SortedManyToManyField

from accounts.models import Participation
from ponyconf.utils import PonyConfModel, enum_to_choices

from .utils import query_sum

__all__ = ['Topic', 'Talk']


class Topic(PonyConfModel):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    name = models.CharField(max_length=128, verbose_name='Name', unique=True)
    slug = AutoSlugField(populate_from='name', unique=True)

    reviewers = models.ManyToManyField(User, blank=True)

    objects = models.Manager()
    on_site = CurrentSiteManager()

    @property
    def talks(self):
        return Talk.objects.filter(topics=self).all()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('list-talks-by-topic', kwargs={'topic': self.slug})


class Talk(PonyConfModel):

    EVENTS = IntEnum('Event', 'conference_short conference_long workshop stand other')

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    proposer = models.ForeignKey(User, related_name='+')
    speakers = SortedManyToManyField(User)
    title = models.CharField(max_length=128, verbose_name='Title')
    slug = AutoSlugField(populate_from='title', unique=True)
    description = models.TextField(blank=True, verbose_name='Description')
    topics = models.ManyToManyField(Topic, blank=True)
    event = models.IntegerField(choices=enum_to_choices(EVENTS), default=EVENTS.conference_short.value)
    accepted = models.NullBooleanField(default=None)

    objects = models.Manager()
    on_site = CurrentSiteManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('show-talk', kwargs={'slug': self.slug})

    def is_moderable_by(self, user):
        if user.is_superuser:
            return True
        try:
            participation = Participation.on_site.get(user=user)
        except Participation.DoesNotExists:
            return False
        return participation.orga or self.topics.filter(reviewers=participation.user).exists()

    def is_editable_by(self, user):
        return user == self.proposer or user in self.speakers.all() or self.is_moderable_by(user)

    def score(self):
        return query_sum(self.vote_set, 'vote')


class Vote(PonyConfModel):

    talk = models.ForeignKey(Talk)
    user = models.ForeignKey(Participation)
    vote = models.IntegerField(validators=[MinValueValidator(-2), MaxValueValidator(2)], default=0)

    class Meta:
        unique_together = ('talk', 'user')

    def __str__(self):
        return "%+i by %s for %s" % (self.vote, self.user, self.talk)

    def get_absolute_url(self):
        return self.talk.get_absolute_url()
