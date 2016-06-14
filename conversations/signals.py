from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.core import mail
from django.core.mail import EmailMultiAlternatives


from .models import Conversation, Message
from .utils import get_reply_addr
from proposals.models import Talk, Topic
from accounts.models import Participation


@receiver(post_save, sender=Participation, dispatch_uid="Create Conversation")
def create_conversation(sender, instance, created, **kwargs):
    if not created:
        return
    conversation = Conversation(participation=instance).save()


@receiver(post_save, sender=Message, dispatch_uid="Notify new message")
def notify_new_message(sender, instance, created, **kwargs):
    if not created:
        # We could send a modification notification
        return
    message = instance
    conversation = message.conversation
    site = conversation.participation.site
    subject = site.name
    sender = message.author
    if sender != conversation.participation.user \
            and sender not in conversation.subscribers:
        conversation.subscribers.add(sender)
    dests = list(conversation.subscribers.all())
    data = {
        'content': message.content,
        'uri': site.domain + reverse('messaging'),
    }
    message_id = message.token
    ref = None
    if conversation.messages.first().id != message.id:
        ref = conversation.messages.first().token
    notify_by_email(data, 'new_message', subject, sender, dests, message_id, ref)


def notify_by_email(data, template, subject, sender, dests, message_id, ref=None):

    if hasattr(settings, 'REPLY_EMAIL') and hasattr(settings, 'REPLY_KEY'):
        data.update({'answering': True})

    text_message = render_to_string('conversations/%s.txt' % template, data)
    html_message = render_to_string('conversations/%s.html' % template, data)

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
    for subject, message, from_email, dests, reply_to, headers in mails:
        text_message, html_message = message
        msg = EmailMultiAlternatives(subject, text_message, from_email, dests, reply_to=reply_to, headers=headers)
        msg.attach_alternative(html_message, 'text/html')
        messages += [msg]
    with mail.get_connection() as connection:
        connection.send_messages(messages)
