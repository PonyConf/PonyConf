from django.conf import settings
from django.utils.crypto import get_random_string

import hashlib


def hexdigest_sha256(*args):

    r = hashlib.sha256()
    for arg in args:
        r.update(str(arg).encode('utf-8'))

    return r.hexdigest()


def get_reply_addr(message_id, dest):

    if not hasattr(settings, 'REPLY_EMAIL'):
        return []

    addr = settings.REPLY_EMAIL
    pos = addr.find('@')
    name = addr[:pos]
    domain = addr[pos:]
    key = hexdigest_sha256(settings.SECRET_KEY, message_id, dest.pk)[0:12]

    return ['%s+%s%s%s%s' % (name, dest.profile.email_token, message_id, key, domain)]


def generate_message_token():
    return get_random_string(length=60, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')
