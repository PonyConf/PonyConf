from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ProposalsConfig(AppConfig):
    name = 'proposals'

    def ready(self):
        import proposals.signals  # noqa
        post_migrate.connect(proposals.signals.call_first_site_post_save, sender=self)
