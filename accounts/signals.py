from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.sites.shortcuts import get_current_site
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop

from .models import Connector, Participation, Profile, Transport


def create_default_options(sender, **kwargs):
    Transport.objects.get_or_create(name=ugettext_noop('Train'))
    Transport.objects.get_or_create(name=ugettext_noop('Plane'))
    Transport.objects.get_or_create(name=ugettext_noop('Carpooling'))
    Connector.objects.get_or_create(name=ugettext_noop('VGA'))
    Connector.objects.get_or_create(name=ugettext_noop('HDMI'))
    Connector.objects.get_or_create(name=ugettext_noop('miniDP'))
    Connector.objects.get_or_create(name=ugettext_noop('I need a computer'))


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    participation, created = Participation.objects.get_or_create(user=user, site=get_current_site(request))
    if user.is_superuser:
        participation.orga = True
        participation.save()
    if created:
        messages.info(request, "Please check your profile!\n", fail_silently=True)  # FIXME
    messages.success(request, _('Welcome!'), fail_silently=True)  # FIXME


@receiver(user_logged_out)
def on_user_logged_out(sender, request, **kwargs):
    messages.success(request, _('Goodbye!'), fail_silently=True)  # FIXME


def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

post_save.connect(create_profile, sender=User, weak=False, dispatch_uid='create_profile')
