from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.conf import settings

from .models import Conference


@receiver(post_save, sender=Site, dispatch_uid="Create Conference for Site")
@disable_for_loaddata
def create_conference(sender, instance, **kwargs):
    Conference.objects.get_or_create(site=instance)


def call_first_site_post_save(apps, **kwargs):
    try:
        site = Site.objects.get(id=getattr(settings, 'SITE_ID', 1))
    except Site.DoesNotExist:
        pass
    else:
        site.save()
