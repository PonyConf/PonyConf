from django.contrib.sites.shortcuts import get_current_site
from django.utils.crypto import get_random_string


def generate_user_uid():
    return get_random_string(length=12, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')


def is_staff(request, user):
    return user.is_authenticated() and user.participation_set.get(site=get_current_site(request)).is_staff()
