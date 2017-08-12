from django import template

from cfp.utils import is_staff


register = template.Library()


@register.filter
def staff(request):
    return is_staff(request, request.user)

@register.filter('duration_format')
def duration_format(value):
    value = int(value)
    hours = int(value/60)
    minutes = value%60
    return '%d h %02d' % (hours, minutes)
