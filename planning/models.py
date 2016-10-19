from django.db import models

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db.models import Q

from autoslug import AutoSlugField


class Room(models.Model):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    slug = AutoSlugField(populate_from='name')
    name = models.CharField(max_length=256, blank=True, default="")
    label = models.CharField(max_length=256, blank=True, default="")
    capacity = models.IntegerField(default=0)

    class Meta:
        unique_together = ['site', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('list-rooms')

    @property
    def talks(self):
        return self.talk_set.exclude(accepted=False)

    @property
    def talks_by_date(self):
        return self.talks.filter(start_date__isnull=False).exclude(Q(duration=0) | Q(event__duration=0)).order_by('start_date').all()

    @property
    def unscheduled_talks(self):
        return self.talks.filter(Q(start_date__isnull=True) | Q(duration=0, event__duration=0)).all()
