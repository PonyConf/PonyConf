from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site

from .models import Conference


def conference(request):
    conference = Conference.objects.get(site=get_current_site(request))
    return {'conference': conference}
