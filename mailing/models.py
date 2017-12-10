from django.db import models
from django.utils.crypto import get_random_string
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

import hashlib


def generate_message_token():
    # /!\ birthday problem
    return get_random_string(length=32, allowed_chars='abcdefghijklmnopqrstuvwxyz0123456789')


def hexdigest_sha256(*args):
    r = hashlib.sha256()
    for arg in args:
        r.update(str(arg).encode('utf-8'))
    return r.hexdigest()


class MessageCorrespondent(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=64, default=generate_message_token, unique=True)


class MessageAuthor(models.Model):
    author_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    author_id = models.PositiveIntegerField(null=True, blank=True)
    author = GenericForeignKey('author_type', 'author_id')
    token = models.CharField(max_length=64, default=generate_message_token, unique=True)

    def __str__(self):
        author_class = self.author_type.model_class()
        if author_class == get_user_model():
            return self.author.get_full_name()
        else:
            return str(self.author)


class MessageThread(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=64, default=generate_message_token, unique=True)


class MessageManager(models.Manager):
    def get_queyset(self):
        qs = super().get_queryset()
        # Does not work so well as prefetch_related is limited to one content type for generic foreign keys
        qs = qs.prefetch_related('author__author')
        return qs


class Message(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE)
    author = models.ForeignKey(MessageAuthor, on_delete=models.PROTECT)
    in_reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    subject = models.CharField(max_length=1000, blank=True)
    content = models.TextField(blank=True)
    token = models.CharField(max_length=64, default=generate_message_token, unique=True)

    objects = MessageManager()

    class Meta:
        ordering = ['created']

    def send_notification(self, sender, dests, reply_to=None, message_id=None, reference=None, footer=None):
        messages = []
        for dest, dest_name, dest_email in dests:
            dest_type = ContentType.objects.get_for_model(dest)
            dest, _ = MessageAuthor.objects.get_or_create(author_type=dest_type, author_id=dest.pk)
            token = self.token + dest.token + hexdigest_sha256(settings.SECRET_KEY, self.token, dest.token)[:16]
            if reply_to:
                reply_to_name, reply_to_email = reply_to
                reply_to_list = ['%s <%s>' % (reply_to_name, reply_to_email.format(token=token))]
            else:
                reply_to_list = []
            headers = dict()
            if message_id:
                headers.update({
                    'Message-ID': message_id.format(id=self.token),
                })
            if message_id and reference:
                headers.update({
                    'References': message_id.format(id=reference),
                })
            body = self.content
            if footer is not None:
                body += footer
            messages.append(EmailMessage(
                subject=self.subject,
                body=body,
                from_email='%s <%s>' % sender,
                to=['%s <%s>' % (dest_name, dest_email)],
                reply_to=reply_to_list,
                headers=headers,
            ))
        connection = get_connection()
        connection.send_messages(messages)

    def __str__(self):
        return _("Message from %(author)s") % {'author': str(self.author)}
