from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site

from ponyconf.admin import SiteAdminMixin
from .models import Conference, Participant, Talk, TalkCategory, Track


class ConferenceAdmin(SiteAdminMixin, admin.ModelAdmin):
    pass


class ParticipantAdmin(SiteAdminMixin, admin.ModelAdmin):
    pass


class TrackAdmin(SiteAdminMixin, admin.ModelAdmin):
    pass


class TalkCategoryAdmin(SiteAdminMixin, admin.ModelAdmin):
    pass


class TalkAdmin(SiteAdminMixin, admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        site = get_current_site(request)
        form.base_fields['speakers'].queryset = Participant.objects.filter(site=site)
        form.base_fields['track'].queryset = Track.objects.filter(site=site)
        form.base_fields['category'].queryset = TalkCategory.objects.filter(site=site)
        return form


admin.site.register(Conference, ConferenceAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Talk, TalkAdmin)
admin.site.register(TalkCategory, TalkCategoryAdmin)
