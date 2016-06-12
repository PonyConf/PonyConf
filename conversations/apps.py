from django.apps import AppConfig


class ConversationsConfig(AppConfig):
    name = 'conversations'

    def ready(self):
        import conversations.signals
