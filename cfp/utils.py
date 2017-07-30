from django.utils.crypto import get_random_string
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils.safestring import mark_safe

from markdown import markdown
import bleach

from .models import Conference


def get_current_conf(request):
    site = get_current_site(request)
    return Conference.objects.get(site=site)


def query_sum(queryset, field):
    return queryset.aggregate(s=Coalesce(Sum(field), 0))['s']


def generate_user_uid():
    return get_random_string(length=12, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')


def allowed_talks(talks, request):
    if not Participation.objects.get(site=get_current_site(request), user=request.user).is_orga():
        talks = talks.filter(Q(topics__reviewers=request.user) | Q(speakers=request.user) | Q(proposer=request.user))
    return talks.distinct()


def markdown_to_html(md):
    html = markdown(md)
    allowed_tags = bleach.ALLOWED_TAGS + ['p', 'pre', 'span' ] + ['h%d' % i for i in range(1, 7) ]
    html = bleach.clean(html, tags=allowed_tags)
    return mark_safe(html)

  
def is_staff(request, user):
    return user.is_authenticated and (user.is_superuser or user in site.conference.staff)
