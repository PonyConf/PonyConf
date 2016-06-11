from django.contrib import admin

from proposals.models import Speach, Talk, Topic

admin.site.register(Topic)
admin.site.register(Talk)
admin.site.register(Speach)
