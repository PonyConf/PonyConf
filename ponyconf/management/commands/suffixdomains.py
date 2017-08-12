from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Add a suffix to all site domains.'

    def add_arguments(self, parser):
        parser.add_argument('suffix')

    def handle(self, *args, **options):
        answer = input("""You are about to change all site domains.
Are you sure you want to do this?

    Type 'yes' to continue, or 'no' to cancel: """)

        self.stdout.write('\n')

        if answer != "yes":
            self.stdout.write(self.style.NOTICE('Action cancelled.'))
            return

        for site in Site.objects.all():
            site.domain = site.domain + options['suffix']
            site.save()

        self.stdout.write(self.style.SUCCESS('All domains modified.'))
