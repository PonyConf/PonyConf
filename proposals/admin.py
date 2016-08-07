from django.contrib import admin

from proposals.models import Conference, Talk, Topic

admin.site.register(Conference)
admin.site.register(Topic)
admin.site.register(Talk)
