from functools import wraps

from accounts.utils import is_orga, is_staff


def orga_required(func):
    def _is_orga(request, *args, **kwargs):
        return is_orga(request, request.user)
    return wraps(func)(_is_orga)


def staff_required(func):
    def _is_staff(request, *args, **kwargs):
        return is_staff(request, request.user)
    return wraps(func)(_is_staff)
