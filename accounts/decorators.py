from functools import wraps
from django.core.exceptions import PermissionDenied

from accounts.utils import is_orga, is_staff


def orga_required(func):
    def _is_orga(request, *args, **kwargs):
        if is_orga(request, request.user):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wraps(func)(_is_orga)


def staff_required(view_func):
    def _is_staff(request, *args, **kwargs):
        if is_staff(request, request.user):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wraps(view_func)(_is_staff)
