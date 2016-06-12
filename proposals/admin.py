from django.contrib import admin

from proposals.models import Speech, Talk, Topic

admin.site.register(Topic)
admin.site.register(Talk)
admin.site.register(Speech)
