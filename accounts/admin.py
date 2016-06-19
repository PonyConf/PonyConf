from django.contrib import admin

from accounts.models import Participation, Profile

admin.site.register(Profile)  # FIXME extend user admin
admin.site.register(Participation)
