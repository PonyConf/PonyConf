from django.contrib import admin
from django.contrib.sites.models import Site

from .mixins import OnSiteAdminMixin
from .models import Conference, Participant, Talk, TalkCategory, Track, \
                    Vote, Volunteer, Activity, Tag


class ConferenceAdmin(OnSiteAdminMixin, admin.ModelAdmin):
    filter_horizontal = ('staff',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ParticipantAdmin(OnSiteAdminMixin, admin.ModelAdmin):
    pass


class TrackAdmin(OnSiteAdminMixin, admin.ModelAdmin):
    pass


class TalkCategoryAdmin(OnSiteAdminMixin, admin.ModelAdmin):
    pass


class TalkAdmin(OnSiteAdminMixin, admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['speakers'].queryset = Participant.objects.filter(site=request.conference.site)
        form.base_fields['track'].queryset = Track.objects.filter(site=request.conference.site)
        form.base_fields['category'].queryset = TalkCategory.objects.filter(site=request.conference.site)
        return form


class VoteAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(talk__site=request.conference.site)


class OnSiteModelAdmin(OnSiteAdminMixin, admin.ModelAdmin):
    pass


admin.site.register(Conference, ConferenceAdmin)
admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Talk, TalkAdmin)
admin.site.register(TalkCategory, TalkCategoryAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Track, OnSiteModelAdmin)
admin.site.register(Tag, OnSiteModelAdmin)
admin.site.register(Volunteer, OnSiteModelAdmin)
admin.site.register(Activity, OnSiteModelAdmin)
