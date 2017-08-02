from django.conf import settings

import imaplib
import ssl
import logging
from email import policy
from email.parser import BytesParser
import chardet
import re

from .models import MessageThread, MessageCorrespondent, Message, hexdigest_sha256


class NoTokenFoundException(Exception):
    pass

class InvalidTokenException(Exception):
    pass

class InvalidKeyException(Exception):
    pass


def fetch_imap_box(user, password, host, port=993, inbox='INBOX', trash='Trash'):
    logging.basicConfig(level=logging.DEBUG)
    context = ssl.create_default_context()
    success, failure = 0, 0
    with imaplib.IMAP4_SSL(host=host, port=port, ssl_context=context) as M:
        typ, data = M.login(user, password)
        if typ != 'OK':
            raise Exception(data[0].decode('utf-8'))
        typ, data = M.enable('UTF8=ACCEPT')
        if typ != 'OK':
            raise Exception(data[0].decode('utf-8'))
        if trash is not None:
            # Vérification de l’existence de la poubelle
            typ, data = M.select(mailbox=trash)
            if typ != 'OK':
                raise Exception(data[0].decode('utf-8'))
        typ, data = M.select(mailbox=inbox)
        if typ != 'OK':
            raise Exception(data[0].decode('utf-8'))
        typ, data = M.uid('search', None, 'UNSEEN')
        if typ != 'OK':
            raise Exception(data[0].decode('utf-8'))
        logging.info("Fetching %d messages" % len(data[0].split()))
        for num in data[0].split():
            typ, data = M.uid('fetch', num, '(RFC822)')
            if typ != 'OK':
                failure += 1
                logging.warning(data[0].decode('utf-8'))
                continue
            raw_email = data[0][1]
            try:
                process_email(raw_email)
            except Exception as e:
                failure += 1
                logging.exception("An error occured during mail processing")
                if type(e) == NoTokenFoundException:
                    tag = 'NoTokenFound'
                if type(e) == InvalidTokenException:
                    tag = 'InvalidToken'
                if type(e) == InvalidKeyException:
                    tag = 'InvalidKey'
                else:
                    tag = 'UnknowError'
                typ, data = M.uid('store', num, '+FLAGS', tag)
                if typ != 'OK':
                    logging.warning(data[0].decode('utf-8'))
                continue
            if trash is not None:
                typ, data = M.uid('copy', num, trash)
                if typ != 'OK':
                    failure += 1
                    logging.warning(data[0].decode('utf-8'))
                    continue
            typ, data = M.uid('store', num, '+FLAGS', '\Deleted')
            if typ != 'OK':
                failure += 1
                logging.warning(data[0].decode('utf-8'))
                continue
            success += 1
        typ, data = M.expunge()
        if typ != 'OK':
            failure += 1
            raise Exception(data[0].decode('utf-8'))
    logging.info("Finished, success: %d, failure: %d" % (success, failure))


def process_email(raw_email):
    msg = BytesParser(policy=policy.default).parsebytes(raw_email)
    body = msg.get_body(preferencelist=['plain'])
    content = body.get_payload(decode=True)

    charset = body.get_content_charset()
    if not charset:
        charset = chardet.detect(content)['encoding']
    content = content.decode(charset)

    regex = re.compile('^[^+@]+\+(?P<token>[a-zA-Z0-9]{80})@[^@]+$')

    for addr in msg.get('To', '').split(','):
        m = regex.match(addr.strip())
        if m:
            break

    if not m:
        raise NoTokenFoundException

    token = m.group('token')
    key = token[64:]
    try:
        thread = MessageThread.objects.get(token=token[:32])
        sender = MessageCorrespondent.objects.get(token=token[32:64])
    except models.DoesNotExist:
        raise InvalidTokenException

    if key != hexdigest_sha256(settings.SECRET_KEY, thread.token, sender.token)[:16]:
        raise InvalidKeyException

    Message.objects.create(thread=thread, from_email=sender.email, content=content)
