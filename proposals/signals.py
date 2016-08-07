from django.db.models.signals import m2m_changed, post_migrate
from django.dispatch import Signal, receiver
from django.contrib.sites.models import Site

from accounts.models import Participation

from .models import Conference, Talk, Topic

talk_added = Signal(providing_args=["sender", "instance", "author"])
talk_edited = Signal(providing_args=["sender", "instance", "author"])


@receiver(post_migrate)
def create_conference(sender, **kwargs):
    for site in Site.objects.all():
        Conference.objects.get_or_create(site=site)


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
