from django.contrib.sites.shortcuts import get_current_site
from django.utils.crypto import get_random_string


def generate_user_uid():
    return get_random_string(length=12, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')


def is_orga(request, user):
    return user.is_authenticated and user.participation_set.get(site=get_current_site(request)).is_orga()


def is_staff(request, user):
    return user.is_authenticated and user.participation_set.get(site=get_current_site(request)).is_staff()


def can_edit_profile(request, profile):
    editor = request.user.participation_set.get(site=get_current_site(request))
    return editor.is_orga() or editor.topic_set.filter(talk__speakers=profile.user).exists()
