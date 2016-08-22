from django.contrib import admin

from proposals.models import Conference, Talk, Topic, Event


class TalkAdmin(admin.ModelAdmin):
    # Disable add button in django admin has it is too dangerous
    # (it is easy to obtain incoherent data due to site framework)
    def has_add_permission(self, request):
        return False
    # Filter for 'on site' tocpis and event
    def get_form(self, request, obj=None, **kwargs):
        form = super(TalkAdmin, self).get_form(request, obj, **kwargs)
        # in fact, obj should never be none as 'add' button is disabled
        if obj:
            form.base_fields['topics'].queryset = Topic.objects.filter(site=obj.site)
            form.base_fields['event'].queryset = Event.objects.filter(site=obj.site)
        return form

admin.site.register(Conference)
admin.site.register(Topic)
admin.site.register(Talk, TalkAdmin)
admin.site.register(Event)
