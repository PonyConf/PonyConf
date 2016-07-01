from django.db.models import Sum
from django.db.models.functions import Coalesce


def query_sum(queryset, field):
    return queryset.aggregate(s=Coalesce(Sum(field), 0))['s']
