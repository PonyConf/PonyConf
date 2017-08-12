from django.contrib.sites.shortcuts import get_current_site
from django.db import models
from django.utils.html import mark_safe

from markdown import markdown
import bleach


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

    def get_link(self):
        return mark_safe('<a href="%s">%s</a>' % (self.get_absolute_url(), self))


def markdown_to_html(md):
    html = markdown(md)
    allowed_tags = bleach.ALLOWED_TAGS + ['p', 'pre', 'span' ] + ['h%d' % i for i in range(1, 7) ]
    html = bleach.clean(html, tags=allowed_tags)
    return mark_safe(html)
