from django.contrib import admin
from django.contrib.sites.shortcuts import get_current_site

from proposals.models import Conference, Talk, Topic, Track, Event
from planning.models import Room


class SiteAdminMixin:
    exclude = ('site',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(site=get_current_site(request))

    def save_model(self, request, obj, form, change):
        if not change:
            obj.site = get_current_site(request)
        super().save_model(request, obj, form, change)


class TalkAdmin(SiteAdminMixin, admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(TalkAdmin, self).get_form(request, obj, **kwargs)
        site = get_current_site(request)
        form.base_fields['topics'].queryset = Topic.objects.filter(site=site)
        form.base_fields['track'].queryset = Track.objects.filter(site=site)
        form.base_fields['event'].queryset = Event.objects.filter(site=site)
        form.base_fields['room'].queryset = Room.objects.filter(site=site)
        return form


class TopicAdmin(SiteAdminMixin, admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        site = get_current_site(request)
        form.base_fields['track'].queryset = Track.objects.filter(site=site)
        return form


class TrackAdmin(SiteAdminMixin, admin.ModelAdmin):
    pass


class EventAdmin(SiteAdminMixin, admin.ModelAdmin):
    pass


admin.site.register(Conference)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(Talk, TalkAdmin)
admin.site.register(Event, EventAdmin)
