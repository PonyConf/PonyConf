from functools import wraps

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

from cfp.utils import is_staff


def staff_required(view_func):
    def _is_staff(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return login_required(view_func)(request, *args, **kwargs)
        elif is_staff(request, request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wraps(view_func)(_is_staff)
