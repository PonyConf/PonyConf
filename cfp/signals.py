from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from ponyconf.decorators import disable_for_loaddata
from mailing.models import MessageThread, Message
from mailing.utils import send_message
from .models import Participant, Talk, Conference, Volunteer


@receiver(post_save, sender=Site, dispatch_uid="Create Conference for Site")
@disable_for_loaddata
def create_conference(sender, instance, **kwargs):
    conference, created = Conference.objects.get_or_create(site=instance)


def create_conversation(sender, instance, **kwargs):
    if not hasattr(instance, 'conversation'):
        instance.conversation = MessageThread.objects.create()
pre_save.connect(create_conversation, sender=Participant)
pre_save.connect(create_conversation, sender=Talk)
pre_save.connect(create_conversation, sender=Volunteer)


@receiver(post_save, sender=Message, dispatch_uid="Send message notifications")
def send_message_notifications(sender, instance, **kwargs):
    message = instance
    author = message.author.author
    thread = message.thread
    if message.in_reply_to:
        reference = message.in_reply_to.token
    else:
        reference = None
    if hasattr(thread, 'participant'):
        conf = thread.participant.site.conference
    elif hasattr(thread, 'talk'):
        conf = thread.talk.site.conference
    elif hasattr(thread, 'volunteer'):
        conf = thread.volunteer.site.conference
    message_id = '<{id}@%s>' % conf.site.domain
    if conf.reply_email:
        reply_to = (str(conf), conf.reply_email)
    else:
        reply_to = None
    if type(author) == get_user_model():
        sender = author.get_full_name()
    else:
        sender = str(author)
    sender = (sender, conf.contact_email)
    staff_dests = [ (user, user.get_full_name(), user.email) for user in conf.staff.all() ]
    if hasattr(thread, 'participant') or hasattr(thread, 'volunteer'):
        if hasattr(thread, 'participant'):
            user = thread.participant
        else:
            user = thread.volunteer
        dests = [ (user, user.name, user.email) ]
        if author == user: # message from the user, notify the staff
            message.send_notification(sender=sender, dests=staff_dests, reply_to=reply_to, message_id=message_id, reference=reference)
        else: # message to the user, notify the user, and the staff if the message is not a conference notification
            message.send_notification(sender=sender, dests=dests, reply_to=reply_to, message_id=message_id, reference=reference)
            if author != conf:
                message.send_notification(sender=sender, dests=staff_dests, reply_to=reply_to, message_id=message_id, reference=reference)
    elif hasattr(thread, 'talk'):
        message.send_notification(sender=sender, dests=staff_dests,
                                  reply_to=reply_to, message_id=message_id, reference=reference)


# connected in apps.py
def call_first_site_post_save(apps, **kwargs):
    try:
        site = Site.objects.get(id=getattr(settings, 'SITE_ID', 1))
    except Site.DoesNotExist:
        pass
    else:
        site.save()
