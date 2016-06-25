from django import template

from accounts.utils import can_edit_profile, is_staff

register = template.Library()


@register.filter
def staff(request):
    return is_staff(request, request.user)


@register.filter
def edit_profile(request, profile):
    return can_edit_profile(request, profile)
