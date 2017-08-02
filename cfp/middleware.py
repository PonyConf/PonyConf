from .utils import get_current_conf


class ConferenceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view, view_args, view_kwargs):
        if view.__module__ != 'cfp.views':
            return
        view_kwargs['conference'] = get_current_conf(request)
