from django.db import models
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager

from autoslug import AutoSlugField

from accounts.models import User


__all__ = [ 'Topic', 'Talk', 'Speach' ]


class Topic(models.Model):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    objects = models.Manager()
    on_site = CurrentSiteManager()
    
    name = models.CharField(max_length=128, verbose_name='Name', unique=True)
    slug = AutoSlugField(populate_from='name', unique=True)

    def __str__(self):
        return self.name


class Talk(models.Model):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    objects = models.Manager()
    on_site = CurrentSiteManager()

    speakers = models.ManyToManyField(User, through='Speach')
    title = models.CharField(max_length=128, verbose_name='Title')
    slug = AutoSlugField(populate_from='title', unique=True)
    description = models.TextField(blank=True, verbose_name='Description')
    topics = models.ManyToManyField(Topic, blank=True)

    def __str__(self):
        return self.title


class Speach(models.Model):

    SPEAKER_NO = ((1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5"), (6, "6"), (7, "7"),)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    talk = models.ForeignKey(Talk, on_delete=models.CASCADE)
    order = models.IntegerField(choices=SPEAKER_NO)

    class Meta:
        ordering = [ 'order' ]
        unique_together = (
            ('user', 'talk'),
            ('order', 'talk'),
        )

    def __str__(self):
        return self.user.username + ' speaking at ' + self.talk.title + ' in position %d' % self.order
