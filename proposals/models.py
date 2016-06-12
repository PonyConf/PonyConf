from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.db import models

from accounts.models import Speaker
from autoslug import AutoSlugField

__all__ = ['Topic', 'Talk', 'Speach']


class Topic(models.Model):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    name = models.CharField(max_length=128, verbose_name='Name', unique=True)
    slug = AutoSlugField(populate_from='name', unique=True)

    objects = models.Manager()
    on_site = CurrentSiteManager()

    def __str__(self):
        return self.name


class Talk(models.Model):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    speakers = models.ManyToManyField(Speaker, through='Speach')
    title = models.CharField(max_length=128, verbose_name='Title')
    slug = AutoSlugField(populate_from='title', unique=True)
    description = models.TextField(blank=True, verbose_name='Description')
    topics = models.ManyToManyField(Topic, blank=True)

    objects = models.Manager()
    on_site = CurrentSiteManager()

    def __str__(self):
        return self.title


class Speach(models.Model):

    SPEAKER_NO = tuple((i, str(i)) for i in range(1, 8))

    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE)
    talk = models.ForeignKey(Talk, on_delete=models.CASCADE)
    order = models.IntegerField(choices=SPEAKER_NO)

    class Meta:
        ordering = ['talk', 'order']
        unique_together = (
            ('speaker', 'talk'),
            ('order', 'talk'),
        )

    def __str__(self):
        return '%s speaking at %s in position %d' % (self.speaker, self.talk, self.order)

    def username(self):
        return self.speaker.user.username
