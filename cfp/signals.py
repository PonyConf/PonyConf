from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from ponyconf.decorators import disable_for_loaddata
from mailing.models import MessageThread, Message
from .models import Participant, Talk, Conference


@receiver(post_save, sender=Site, dispatch_uid="Create Conference for Site")
@disable_for_loaddata
def create_conference(sender, instance, **kwargs):
    conference, created = Conference.objects.get_or_create(site=instance)


def create_conversation(sender, instance, **kwargs):
    if not hasattr(instance, 'conversation'):
        instance.conversation = MessageThread.objects.create()
pre_save.connect(create_conversation, sender=Participant)
pre_save.connect(create_conversation, sender=Talk)


@receiver(pre_save, sender=Message, dispatch_uid="Set message author")
def set_message_author(sender, instance, **kwargs):
    message = instance
    if message.author is None:
        # Try users
        try:
            instance.author = User.objects.get(email=message.from_email)
        except User.DoesNotExist:
            pass
        else:
            return
        # Try participants
        try:
            instance.author = Participant.objects.get(email=message.from_email)
        except User.DoesNotExist:
            pass
        else:
            return
        # Try conferences
        try:
            instance.author = Conference.objects.get(contact_email=message.from_email)
        except Conference.DoesNotExist:
            pass
        else:
            return


@receiver(post_save, sender=Message, dispatch_uid="Send message notifications")
def send_message_notifications(sender, instance, **kwargs):
    message = instance
    thread = message.thread
    first_message = thread.message_set.first()
    if message == first_message:
        reference = None
    else:
        reference = first_message.token
    subject_prefix = 'Re: ' if reference else ''
    if hasattr(thread, 'participant'):
        conf = thread.participant.site.conference
    elif hasattr(thread, 'talk'):
        conf = thread.talk.site.conference
    message_id = '<{id}@%s>' % conf.site.domain
    if conf.reply_email:
        reply_to = (conf.name, conf.reply_email)
    else:
        reply_to = None
    sender = (message.author_display, conf.contact_email)
    staff_dests = [ (user.get_full_name(), user.email) for user in conf.staff.all() ]
    if hasattr(thread, 'participant'):
        conf = thread.participant.site.conference
        participant = thread.participant
        participant_dests = [ (participant.name, participant.email) ]
        participant_subject = _('[%(prefix)s] Message from the staff') % {'prefix': conf.name}
        staff_subject = _('[%(prefix)s] Conversation with %(dest)s') % {'prefix': conf.name, 'dest': participant.name}
        proto = 'https' if conf.secure_domain else 'http'
        footer = '\n\n--\n%s://' % proto + conf.site.domain + reverse('participant-details', args=[participant.token])
        if message.from_email == conf.contact_email: # this is a talk notification message
            # send it only to the participant
            message.send_notification(subject=subject_prefix+participant_subject, sender=sender, dests=participant_dests,
                                      reply_to=reply_to, message_id=message_id, reference=reference)
        else:
            # this is a message between the staff and the participant
            message.send_notification(subject=subject_prefix+staff_subject, sender=sender, dests=staff_dests,
                                      reply_to=reply_to, message_id=message_id, reference=reference, footer=footer)
            if message.from_email != thread.participant.email: # message from staff: sent it to the participant too
                message.send_notification(subject=subject_prefix+participant_subject, sender=sender, dests=participant_dests,
                                          reply_to=reply_to, message_id=message_id, reference=reference)
    elif hasattr(thread, 'talk'):
        conf = thread.talk.site.conference
        subject = _('[%(prefix)s] Talk: %(talk)s') % {'prefix': conf.name, 'talk': thread.talk.title}
        proto = 'https' if conf.secure_domain else 'http'
        footer = '\n\n--\n%s://' % proto + conf.site.domain + reverse('talk-details', args=[thread.talk.token])
        message.send_notification(subject=subject_prefix+subject, sender=sender, dests=staff_dests,
                                  reply_to=reply_to, message_id=message_id, reference=reference, footer=footer)


# connected in apps.py
def call_first_site_post_save(apps, **kwargs):
    try:
        site = Site.objects.get(id=getattr(settings, 'SITE_ID', 1))
    except Site.DoesNotExist:
        pass
    else:
        site.save()
