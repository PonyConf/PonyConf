from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.contrib.auth.decorators import login_required

from ponyconf.mixins import OnSiteFormMixin

from accounts.mixins import OrgaRequiredMixin, StaffRequiredMixin

from .models import Activity
from .forms import ActivityForm



@login_required
def participate(request, slug=None):
    if slug:
        # TODO: enrole action should be done on post (with bootstrap modal confirmation box?)
        activity = get_object_or_404(Activity, site=get_current_site(request), slug=slug)
        if request.user in activity.participants.all():
            activity.participants.remove(request.user)
        else:
            activity.participants.add(request.user)
        activity.save()
        return redirect('participate-as-volunteer')
    activities = Activity.objects.filter(site=get_current_site(request))
    return render(request, 'volunteers/participate.html', {
        'activities': activities,
    })


class ActivityMixin(object):
    def get_queryset(self):
        return Activity.objects.filter(site=get_current_site(self.request)).all()


class ActivityFormMixin(OnSiteFormMixin):
    form_class = ActivityForm


class ActivityList(StaffRequiredMixin, ActivityMixin, ListView):
    pass


class ActivityCreate(OrgaRequiredMixin, ActivityMixin, ActivityFormMixin, CreateView):
    model = Activity


class ActivityUpdate(OrgaRequiredMixin, ActivityMixin, ActivityFormMixin, UpdateView):
    pass


class ActivityDetail(StaffRequiredMixin, ActivityMixin, DetailView):
    pass
