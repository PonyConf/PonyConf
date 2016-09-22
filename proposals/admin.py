from django.contrib import admin

from proposals.models import Conference, Talk, Topic, Track, Event


class TalkAdmin(admin.ModelAdmin):
    # Disable add button in django admin has it is too dangerous
    # (it is easy to obtain incoherent data due to site framework)
    def has_add_permission(self, request):
        return False
    # Filter for 'on site' topics, tracks and events
    def get_form(self, request, obj=None, **kwargs):
        form = super(TalkAdmin, self).get_form(request, obj, **kwargs)
        # in fact, obj should never be none as 'add' button is disabled
        if obj:
            form.base_fields['topics'].queryset = Topic.objects.filter(site=obj.site)
            form.base_fields['track'].queryset = Track.objects.filter(site=obj.site)
            form.base_fields['event'].queryset = Event.objects.filter(site=obj.site)
        return form


class TopicAdmin(admin.ModelAdmin):
    # Filter for 'on site' tracks
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['track'].queryset = Track.objects.filter(site=obj.site)
        return form

admin.site.register(Conference)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Track)
admin.site.register(Talk, TalkAdmin)
admin.site.register(Event)
