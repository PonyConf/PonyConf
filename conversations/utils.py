from django.conf import settings
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.core import mail

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


def notify_by_email(template, data, subject, sender, dests, message_id, ref=None):

    if hasattr(settings, 'REPLY_EMAIL') and hasattr(settings, 'REPLY_KEY'):
        data.update({'answering': True})

    text_message = render_to_string('conversations/emails/%s.txt' % template, data)
    html_message = render_to_string('conversations/emails/%s.html' % template, data)

    from_email = '{name} <{email}>'.format(
            name=sender.get_full_name() or sender.username,
            email=settings.DEFAULT_FROM_EMAIL)

    # Generating headers
    headers = {
		'Message-ID': "<%s.%s>" % (message_id, settings.DEFAULT_FROM_EMAIL),
	}
    if ref:
        # This email reference a previous one
        headers.update({
            'References': '<%s.%s>' % (ref, settings.DEFAULT_FROM_EMAIL),
        })

    mails = []
    for dest in dests:
        if not dest.email:
            continue

        reply_to = get_reply_addr(message_id, dest)

        mails += [(subject, (text_message, html_message), from_email, [dest.email], reply_to, headers)]

    messages = []
    for subject, message, from_email, dest_emails, reply_to, headers in mails:
        text_message, html_message = message
        msg = EmailMultiAlternatives(subject, text_message, from_email, dest_emails, reply_to=reply_to, headers=headers)
        msg.attach_alternative(html_message, 'text/html')
        messages += [msg]
    with mail.get_connection() as connection:
        connection.send_messages(messages)
