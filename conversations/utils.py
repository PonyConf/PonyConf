import hashlib

from django.conf import settings


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
    key = hexdigest_sha256(settings.SECRET_KEY, message_id, dest.pk)

    return ['%s+%10s%s%10s%s' % (name, dest.pk, message_id, key, domain)]
