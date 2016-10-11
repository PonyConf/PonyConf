from django.db import models

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

from autoslug import AutoSlugField


class Room(models.Model):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    slug = AutoSlugField(populate_from='name')
    name = models.CharField(max_length=256, blank=True, default="")
    label = models.CharField(max_length=256, blank=True, default="")
    capacity = models.IntegerField(default=0)

    class Meta:
        unique_together = ['site', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('list-rooms')

    @property
    def talks_by_date(self):
        return self.talk_set.filter(start_date__isnull=False).order_by('start_date').all()

    @property
    def unscheduled_talks(self):
        return self.talk_set.filter(start_date__isnull=True).all()
