from django.utils.crypto import get_random_string
from django.db.models import Sum
from django.db.models.functions import Coalesce


def query_sum(queryset, field):
    return queryset.aggregate(s=Coalesce(Sum(field), 0))['s']


def generate_user_uid():
    return get_random_string(length=12, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')

  
def is_staff(request, user):
    return user.is_authenticated and (user.is_superuser or request.conference.staff.filter(pk=user.pk).exists())
