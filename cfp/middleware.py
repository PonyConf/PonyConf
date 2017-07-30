from django.core.exceptions import ImproperlyConfigured

from .utils import get_current_conf


class ConferenceMiddleware:
    def process_view(self, request, view, view_args, view_kwargs):
        if view.__module__ != 'cfp.views':
            return
        view_kwargs['conference'] = get_current_conf(request)
