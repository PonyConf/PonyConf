from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User


class Activity(models.Model):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    name = models.CharField(max_length=256, verbose_name=_('Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    participants = models.ManyToManyField(User, blank=True, verbose_name=_('Participants'))

    class Meta:
        unique_together = ('site', 'name')

    def __str__(self):
        return self.name
