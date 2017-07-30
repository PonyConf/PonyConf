from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.conf import settings

from ponyconf.decorators import disable_for_loaddata
from .models import Conference


@receiver(post_save, sender=Site, dispatch_uid="Create Conference for Site")
@disable_for_loaddata
def create_conference(sender, instance, **kwargs):
    conference, created = Conference.objects.get_or_create(site=instance)


# connected in apps.py
def call_first_site_post_save(apps, **kwargs):
    try:
        site = Site.objects.get(id=getattr(settings, 'SITE_ID', 1))
    except Site.DoesNotExist:
        pass
    else:
        site.save()
