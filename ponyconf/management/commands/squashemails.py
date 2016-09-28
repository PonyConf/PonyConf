from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Squash all users email'

    def handle(self, *args, **options):
        answer = input("""You are about to squash all users email.
This action is IRREVERSIBLE!
Are you sure you want to do this?

    Type 'yes' to continue, or 'no' to cancel: """)

        self.stdout.write('\n')

        if answer != "yes":
            self.stdout.write(self.style.NOTICE('Action cancelled.'))
            return

        for user in User.objects.all():
            user.email = ''
            user.save()

        self.stdout.write(self.style.SUCCESS('All emails squashed.'))
