from django.contrib.sites.shortcuts import get_current_site


class SiteAdminMixin:
    exclude = ('site',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(site=get_current_site(request))

    def save_model(self, request, obj, form, change):
        if not change:
            obj.site = get_current_site(request)
        super().save_model(request, obj, form, change)
