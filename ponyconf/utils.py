from django.contrib.sites.shortcuts import get_current_site


def enum_to_choices(enum):
    return ((item.value, item.name) for item in list(enum))


def full_link(obj, request=None):
    protocol = 'https' if request is None or request.is_secure() else 'http'
    return '%s://%s%s' % (protocol, get_current_site(request), obj.get_absolute_url())
