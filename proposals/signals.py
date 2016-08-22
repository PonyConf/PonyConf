from django.db.models.signals import m2m_changed, post_save
from django.dispatch import Signal, receiver
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_noop
from django.conf import settings

from accounts.models import Participation

from .models import Conference, Talk, Topic, Event


talk_added = Signal(providing_args=["sender", "instance", "author"])
talk_edited = Signal(providing_args=["sender", "instance", "author"])


@receiver(post_save, sender=Site, dispatch_uid="Create Conference for Site")
def create_conference(sender, instance, **kwargs):
    Conference.objects.get_or_create(site=instance)


@receiver(post_save, sender=Site, dispatch_uid="Create default events type for Site")
def create_events(sender, instance, **kwargs):
    if not Event.objects.filter(site=instance).exists():
        Event.objects.bulk_create([
            Event(site=instance, name=ugettext_noop('conference (short)')),
            Event(site=instance, name=ugettext_noop('conference (long)')),
            Event(site=instance, name=ugettext_noop('workshop')),
            Event(site=instance, name=ugettext_noop('stand')),
            Event(site=instance, name=ugettext_noop('other')),
        ])


def call_first_site_post_save(apps, **kwargs):
    site = Site.objects.filter(id=getattr(settings, 'SITE_ID', 1))
    if site.exists():
        site.first().save()


@receiver(m2m_changed, sender=Talk.speakers.through, dispatch_uid="Create Participation for speakers")
def create_participation_for_speakers(sender, instance, action, reverse, model, pk_set, using, **kwargs):
    if action != "pre_add":
        pass
    for speaker in instance.speakers.all():
        Participation.objects.get_or_create(user=speaker, site=instance.site)


@receiver(m2m_changed, sender=Topic.reviewers.through, dispatch_uid="Create Participation for reviewers")
def create_participation_for_reviewers(sender, instance, action, reverse, model, pk_set, using, **kwargs):
    if action != "pre_add":
        pass
    for reviewer in instance.reviewers.all():
        Participation.objects.get_or_create(user=reviewer, site=instance.site)
