from django.dispatch import Signal, receiver
from django.db.models.signals import m2m_changed


from .models import Topic
from accounts.models import Participation


__all__ = [ 'talk_added', 'talk_edited' ]


talk_added = Signal(providing_args=["sender", "instance", "author"])
talk_edited = Signal(providing_args=["sender", "instance", "author"])


@receiver(m2m_changed, sender=Topic.reviewers.through, dispatch_uid="Create Participation for reviewers")
def create_participation_for_reviewers(sender, instance, action, reverse, model, pk_set, using, **kwargs):
    if action != "pre_add":
        pass
    for reviewer in instance.reviewers.all():
        Participation.objects.get_or_create(user=reviewer, site=instance.site)
