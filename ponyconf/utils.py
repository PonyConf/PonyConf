from django.contrib.sites.shortcuts import get_current_site
from django.db import models


def enum_to_choices(enum):
    return ((item.value, item.name.replace('_', ' ')) for item in list(enum))


class PonyConfModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def full_link(self, request=None):
        protocol = 'https' if request is None or request.is_secure() else 'http'
        return '%s://%s%s' % (protocol, get_current_site(request), self.get_absolute_url())
