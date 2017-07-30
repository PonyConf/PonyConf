from django import template

from cfp.utils import is_staff


register = template.Library()


@register.filter
def staff(request):
    return is_staff(request, request.user)
