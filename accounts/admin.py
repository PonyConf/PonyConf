from django.contrib import admin

from accounts.models import Profile, Speaker

admin.site.register(Profile)  # FIXME extend user admin
admin.site.register(Speaker)
