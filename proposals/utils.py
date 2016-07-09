from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.contrib.sites.shortcuts import get_current_site

from accounts.models import Participation


def query_sum(queryset, field):
    return queryset.aggregate(s=Coalesce(Sum(field), 0))['s']


def allowed_talks(talks, request):
    participation = Participation.objects.get(site=get_current_site(request), user=request.user)
    if not participation.is_orga():
        talks = talks.filter(Q(topics__reviewers=participation.user) | Q(speakers=request.user) | Q(proposer=request.user))
    return talks.distinct()
