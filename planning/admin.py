from django.contrib import admin

from planning.models import Room


class RoomAdmin(admin.ModelAdmin):
    fields = ('name', 'label', 'capacity', 'site')


admin.site.register(Room, RoomAdmin)
