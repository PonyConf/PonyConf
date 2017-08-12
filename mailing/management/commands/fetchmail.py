from django.core.management.base import BaseCommand

from mailing.utils import fetch_imap_box


class Command(BaseCommand):
    help = 'Fetch emails from IMAP inbox'

    def add_arguments(self, parser):
        parser.add_argument('--host', required=True)
        parser.add_argument('--port', type=int)
        parser.add_argument('--user', required=True)
        parser.add_argument('--password', required=True)
        parser.add_argument('--inbox')
        grp = parser.add_mutually_exclusive_group()
        grp.add_argument('--trash')
        grp.add_argument('--no-trash', action='store_true')


    def handle(self, *args, **options):
        params = {
            'host': options['host'],
            'user': options['user'],
            'password': options['password'],
        }
        if options['port']:
            params['port'] = options['port']
        if options['inbox']:
            params['inbox'] = options['inbox']
        if options['trash']:
            params['trash'] = options['trash']
        elif options['no_trash']:
            params['trash'] = None
        fetch_imap_box(**params)
