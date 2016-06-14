from enum import IntEnum

from django.contrib.auth.models import User
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models

from autoslug import AutoSlugField

from accounts.utils import enum_to_choices


__all__ = ['Topic', 'Talk', 'Speech']


class Topic(models.Model):

    name = models.CharField(max_length=128, verbose_name='Name', unique=True)
    slug = AutoSlugField(populate_from='name', unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('list-talks-by-topic', kwargs={'topic': self.slug})


class Talk(models.Model):

    EVENTS = IntEnum('Event', 'conference workshop stand other')

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    proposer = models.ForeignKey(User, related_name='+')
    speakers = models.ManyToManyField(User, through='Speech')
    title = models.CharField(max_length=128, verbose_name='Title')
    slug = AutoSlugField(populate_from='title', unique=True)
    description = models.TextField(blank=True, verbose_name='Description')
    topics = models.ManyToManyField(Topic, blank=True)
    event = models.IntegerField(choices=enum_to_choices(EVENTS), default=EVENTS.conference.value)

    objects = models.Manager()
    on_site = CurrentSiteManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('show-talk', kwargs={'slug': self.slug})

    def is_editable_by(self, user):
        if user.is_superuser:
            return True
        if user == self.proposer:
            return True
        if user in talk.speakers.all():
            return True
        try:
            participation = Participation.on_site.get(user=user)
        except Participation.DoesNotExists:
            return False
        return self.topics.filter(pk=participation.review_topics.pk).exists()


class Speech(models.Model):

    SPEAKER_NO = tuple((i, str(i)) for i in range(1, 8))

    speaker = models.ForeignKey(User, on_delete=models.CASCADE)
    talk = models.ForeignKey(Talk, on_delete=models.CASCADE)
    order = models.IntegerField(choices=SPEAKER_NO, default=1)

    class Meta:
        ordering = ['talk', 'order']
        unique_together = (
            ('speaker', 'talk'),
            ('order', 'talk'),
        )

    def __str__(self):
        return '%s speaking at %s in position %d' % (self.speaker, self.talk, self.order)

    def get_absolute_url(self):
        return self.talk.get_absolute_url()

    def username(self):
        return self.speaker.username
