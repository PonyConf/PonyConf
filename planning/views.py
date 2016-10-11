from django.shortcuts import render
from django.contrib.sites.shortcuts import get_current_site
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import OrgaRequiredMixin, StaffRequiredMixin
from proposals.mixins import OnSiteFormMixin

from .models import Room
from .forms import RoomForm


class RoomMixin(object):
    def get_queryset(self):
        return Room.objects.filter(site=get_current_site(self.request)).all()


class RoomFormMixin(OnSiteFormMixin):
    form_class = RoomForm


class RoomList(StaffRequiredMixin, RoomMixin, ListView):
    pass


class RoomCreate(OrgaRequiredMixin, RoomMixin, RoomFormMixin, CreateView):
    model = Room

class RoomUpdate(OrgaRequiredMixin, RoomMixin, RoomFormMixin, UpdateView):
    pass

class RoomDetail(StaffRequiredMixin, RoomMixin, DetailView):
    pass
