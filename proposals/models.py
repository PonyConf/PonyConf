from enum import IntEnum

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.utils import timezone

from autoslug import AutoSlugField

from accounts.models import Participation
from ponyconf.utils import PonyConfModel, enum_to_choices

from .utils import query_sum


class Conference(models.Model):

    site = models.OneToOneField(Site, on_delete=models.CASCADE)
    home = models.TextField(blank=True, default="")
    cfp_opening_date = models.DateTimeField(null=True, blank=True, default=None)
    cfp_closing_date = models.DateTimeField(null=True, blank=True, default=None)

    def cfp_is_open(self):
        now = timezone.now()
        if self.cfp_opening_date and now < self.cfp_opening_date:
            return False
        if self.cfp_closing_date and now > self.cfp_closing_date:
            return False
        return True

    def __str__(self):
        return str(self.site)


class Track(PonyConfModel):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    name = models.CharField(max_length=128, verbose_name=_('Name'))
    slug = AutoSlugField(populate_from='name')
    description = models.TextField(blank=True, verbose_name=_('Description'))

    class Meta:
        unique_together = ('site', 'name')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('list-talks') + '?track=%s' % self.slug


class Topic(PonyConfModel):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    name = models.CharField(max_length=128, verbose_name=_('Name'))
    slug = AutoSlugField(populate_from='name', unique=True)
    description = models.TextField(blank=True, verbose_name=_('Description'))
    track = models.ForeignKey(Track, blank=True, null=True, verbose_name=_('Destination track'))

    reviewers = models.ManyToManyField(User, blank=True, verbose_name=_('Reviewers'))

    class Meta:
        unique_together = ('site', 'name')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('list-talks') + '?topic=%s' % self.slug


class Event(models.Model):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)

    class Meta:
        unique_together = ('site', 'name')
        ordering = ('pk',)

    def __str__(self):
        return ugettext(self.name)

    def get_absolute_url(self):
        return reverse('list-talks') + '?kind=%d' % self.pk


class Talk(PonyConfModel):

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    proposer = models.ForeignKey(User, related_name='+')
    speakers = models.ManyToManyField(User, verbose_name=_('Speakers'))
    title = models.CharField(max_length=128, verbose_name=_('Title'))
    slug = AutoSlugField(populate_from='title', unique=True)
    abstract = models.CharField(max_length=255, blank=True, verbose_name=_('Abstract'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    topics = models.ManyToManyField(Topic, blank=True, verbose_name=_('Topics'))
    track = models.ForeignKey(Track, blank=True, null=True, verbose_name=_('Track'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    event = models.ForeignKey(Event, verbose_name=_('Intervention kind'))
    accepted = models.NullBooleanField(default=None)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('show-talk', kwargs={'slug': self.slug})

    def is_moderable_by(self, user):
        if user.is_superuser:
            return True
        try:
            participation = Participation.objects.get(site=self.site, user=user)
        except Participation.DoesNotExists:
            return False
        return participation.orga or self.topics.filter(reviewers=participation.user).exists()

    def is_editable_by(self, user):
        return user == self.proposer or user in self.speakers.all() or self.is_moderable_by(user)

    def score(self):
        if self.vote_set.exists():
            return query_sum(self.vote_set, 'vote') / len(self.vote_set.all())
        else:
            return 0

    class Meta:
        ordering = ('event__id',)


class Vote(PonyConfModel):

    talk = models.ForeignKey(Talk)
    user = models.ForeignKey(User)
    vote = models.IntegerField(validators=[MinValueValidator(-2), MaxValueValidator(2)], default=0)

    class Meta:
        unique_together = ('talk', 'user')

    def __str__(self):
        return "%+i by %s for %s" % (self.vote, self.user, self.talk)

    def get_absolute_url(self):
        return self.talk.get_absolute_url()
