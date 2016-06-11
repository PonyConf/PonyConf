from django.contrib import admin

from accounts.models import PonyConfSpeaker, PonyConfUser

admin.site.register(PonyConfUser)
admin.site.register(PonyConfSpeaker)
