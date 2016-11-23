from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.contrib.auth.decorators import login_required

from ponyconf.mixins import OnSiteFormMixin

from accounts.decorators import orga_required, staff_required
from accounts.mixins import OrgaRequiredMixin, StaffRequiredMixin
from accounts.models import Participation

from .models import Activity
from .forms import ActivityForm, VolunteerFilterForm



@login_required
def enrole(request, slug=None):
    if slug:
        # TODO: enrole action should be done on post (with bootstrap modal confirmation box?)
        activity = get_object_or_404(Activity, site=get_current_site(request), slug=slug)
        if request.user in activity.participants.all():
            activity.participants.remove(request.user)
        else:
            activity.participants.add(request.user)
        activity.save()
        return redirect('enrole-as-volunteer')
    activities = Activity.objects.filter(site=get_current_site(request))
    return render(request, 'volunteers/volunteer_enrole.html', {
        'activities': activities,
    })


@staff_required
def volunteer_list(request):
    show_filters = False
    site = get_current_site(request)
    filter_form = VolunteerFilterForm(request.GET or None, site=site)
    # Filtering
    volunteers = Participation.objects.filter(site=site,user__activities__isnull=False).order_by('pk').distinct()
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        if len(data['activity']):
            show_filters = True
            volunteers = volunteers.filter(user__activities__slug__in=data['activity'])
    return render(request, 'volunteers/volunteer_list.html', {
        'volunteer_list': volunteers,
        'filter_form': filter_form,
        'show_filters': show_filters,
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
