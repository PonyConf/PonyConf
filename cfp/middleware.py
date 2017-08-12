from django.contrib.sites.shortcuts import get_current_site

from .models import Conference


class ConferenceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view, view_args, view_kwargs):
        site = get_current_site(request)
        conf = Conference.objects.select_related('site').prefetch_related('staff').get(site=site)
        request.conference = conf
