from django.contrib import admin

from accounts.models import Profile, Participation

admin.site.register(Profile)  # FIXME extend user admin
admin.site.register(Participation)
