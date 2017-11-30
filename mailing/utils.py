from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType

import imaplib
import ssl
import logging
from email import policy
from email.parser import BytesParser
import chardet
import re

from .models import MessageThread, MessageAuthor, Message, hexdigest_sha256


class NoTokenFoundException(Exception):
    pass

class InvalidTokenException(Exception):
    pass

class InvalidKeyException(Exception):
    pass


def send_message(thread, author, subject, content, in_reply_to=None):
    author_type = ContentType.objects.get_for_model(author)
    author, _ = MessageAuthor.objects.get_or_create(author_type=author_type, author_id=author.pk)
    Message.objects.create(
        thread=thread,
        author=author,
        subject=subject,
        content=content,
        in_reply_to=in_reply_to,
    )


def fetch_imap_box(user, password, host, port=993, use_ssl=True, inbox='INBOX', trash='Trash'):
    logging.basicConfig(level=logging.DEBUG)
    context = ssl.create_default_context()
    success, failure = 0, 0
    kwargs = {'host': host, 'port': port}
    if use_ssl:
        IMAP4 = imaplib.IMAP4_SSL
        kwargs.update({'ssl_context': ssl.create_default_context()})
    else:
        IMAP4 = imaplib.IMAP4
    with IMAP4(**kwargs) as M:
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
    if failure:
        total = success + failure
        logging.info("Total: %d, success: %d, failure: %d" % (total, success, failure))


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

    try:
        in_reply_to, author = process_new_token(token)
    except InvalidTokenException:
        in_reply_to, author = process_old_token(token)

    subject = msg.get('Subject', '')

    Message.objects.create(thread=in_reply_to.thread, in_reply_to=in_reply_to, author=author, subject=subject, content=content)


def process_new_token(token):
    key = token[64:]
    try:
        in_reply_to = Message.objects.get(token__iexact=token[:32])
        author = MessageAuthor.objects.get(token__iexact=token[32:64])
    except models.ObjectDoesNotExist:
        raise InvalidTokenException

    if key.lower() != hexdigest_sha256(settings.SECRET_KEY, in_reply_to.token, author.token)[:16]:
        raise InvalidKeyException

    return in_reply_to, author


def process_old_token(token):
    try:
        thread = MessageThread.objects.get(token__iexact=token[:32])
        sender = MessageCorrespondent.objects.get(token__iexact=token[32:64])
    except models.ObjectDoesNotExist:
        raise InvalidTokenException

    if key.lower() != hexdigest_sha256(settings.SECRET_KEY, thread.token, sender.token)[:16]:
        raise InvalidKeyException

    in_reply_to = thread.message_set.last()
    author = None

    if author is None:
        try:
            author = User.objects.get(email=sender.email)
        except User.DoesNotExist:
            pass
    if author is None:
        try:
            author = Participant.objects.get(email=message.from_email)
        except Participant.DoesNotExist:
            pass
    if author is None:
        try:
            author = Conference.objects.get(contact_email=message.from_email)
        except Conference.DoesNotExist:
            raise # this was last hope...

    author = MessageAuthor.objects.get_or_create(author=author)

    return in_reply_to, author
