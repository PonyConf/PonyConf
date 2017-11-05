from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from functools import wraps

from cfp.utils import is_staff
from cfp.models import Participant


def speaker_required(view_func):
    def wrapped_view(request, **kwargs):
        speaker_token = kwargs.pop('speaker_token')
        if speaker_token:
            speaker = get_object_or_404(Participant, site=request.conference.site, token=speaker_token)
        elif request.user.is_authenticated():
            speaker = get_object_or_404(Participant, site=request.conference.site, email=request.user.email)
        else:
            raise PermissionDenied
        kwargs['speaker'] = speaker
        return view_func(request, **kwargs)
    return wraps(view_func)(wrapped_view)


def staff_required(view_func):
    def _is_staff(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return login_required(view_func)(request, *args, **kwargs)
        elif is_staff(request, request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wraps(view_func)(_is_staff)
