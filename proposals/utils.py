from django.db.models import Q, Sum
from django.db.models.functions import Coalesce

from accounts.models import Participation


def query_sum(queryset, field):
    return queryset.aggregate(s=Coalesce(Sum(field), 0))['s']


def allowed_talks(talks, request):
    participation = Participation.on_site.get(user=request.user)
    if not participation.is_orga():
        talks = talks.filter(Q(topics__reviewers=participation) | Q(speakers=request.user) | Q(proposer=request.user))
    return talks.distinct()
