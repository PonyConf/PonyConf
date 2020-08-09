from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import Http404

from functools import wraps
from uuid import UUID

from cfp.utils import is_staff
from cfp.models import Participant, Volunteer


def speaker_required(view_func):
    def wrapped_view(request, **kwargs):
        speaker_token = kwargs.pop('speaker_token', None)
        if speaker_token:
            try:
                speaker_token = UUID(speaker_token)
            except ValueError:
                raise Http404
            speaker = get_object_or_404(Participant, site=request.conference.site, token=speaker_token)
        elif request.user.is_authenticated:
            speaker = get_object_or_404(Participant, site=request.conference.site, email=request.user.email)
        else:
            raise PermissionDenied
        kwargs['speaker'] = speaker
        return view_func(request, **kwargs)
    return wraps(view_func)(wrapped_view)


def volunteer_required(view_func):
    def wrapped_view(request, **kwargs):
        volunteer_token = kwargs.pop('volunteer_token', None)
        if volunteer_token:
            try:
                volunteer_token = UUID(volunteer_token)
            except ValueError:
                raise Http404
            volunteer = get_object_or_404(Volunteer, site=request.conference.site, token=volunteer_token)
        elif request.user.is_authenticated:
            volunteer = get_object_or_404(Volunteer, site=request.conference.site, email=request.user.email)
        else:
            raise PermissionDenied
        kwargs['volunteer'] = volunteer
        return view_func(request, **kwargs)
    return wraps(view_func)(wrapped_view)


def staff_required(view_func):
    def _is_staff(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return login_required(view_func)(request, *args, **kwargs)
        elif is_staff(request, request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wraps(view_func)(_is_staff)
