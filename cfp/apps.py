from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CFPConfig(AppConfig):
    name = 'cfp'

    def ready(self):
        import cfp.signals  # noqa
        post_migrate.connect(cfp.signals.call_first_site_post_save, sender=self)
