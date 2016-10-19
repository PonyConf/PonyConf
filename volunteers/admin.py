from django.contrib import admin

from ponyconf.admin import SiteAdminMixin

from .models import Activity


class ActivityAdmin(SiteAdminMixin, admin.ModelAdmin):
    pass


admin.site.register(Activity, ActivityAdmin)
