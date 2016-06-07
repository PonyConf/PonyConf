from django.contrib.sites.shortcuts import get_current_site


def site(request):

    return {
        'site': get_current_site(request),
    }
