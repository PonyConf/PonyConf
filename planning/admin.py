from django.contrib import admin

from planning.models import Room
from ponyconf.admin import SiteAdminMixin


class RoomAdmin(SiteAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'label', 'capacity')


admin.site.register(Room, RoomAdmin)
