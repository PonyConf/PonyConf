from django.shortcuts import render
from django.contrib.sites.shortcuts import get_current_site
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from ponyconf.mixins import OnSiteFormMixin

from accounts.mixins import OrgaRequiredMixin, StaffRequiredMixin



class ActivityMixin(object):
    def get_queryset(self):
        return Activity.objects.filter(site=get_current_site(self.request)).all()


class ActivityFormMixin(OnSiteFormMixin):
    form_class = ActivityForm


class ActivityList(StaffRequiredMixin, RoomMixin, ListView):
    pass


class ActivityCreate(OrgaRequiredMixin, RoomMixin, RoomFormMixin, CreateView):
    model = Activity


class ActivityUpdate(OrgaRequiredMixin, RoomMixin, RoomFormMixin, UpdateView):
    pass


class ActivityDetail(StaffRequiredMixin, RoomMixin, DetailView):
    pass
