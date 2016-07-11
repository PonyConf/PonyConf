from django.db.models.signals import m2m_changed
from django.dispatch import Signal, receiver

from accounts.models import Participation

from .models import Talk, Topic

talk_added = Signal(providing_args=["sender", "instance", "author"])
talk_edited = Signal(providing_args=["sender", "instance", "author"])


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
