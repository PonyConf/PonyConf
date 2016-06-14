from django.contrib import admin

from .models import ConversationWithParticipant, ConversationAboutTalk, Message


admin.site.register(ConversationWithParticipant)
admin.site.register(ConversationAboutTalk)
admin.site.register(Message)
