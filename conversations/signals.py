from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Participation
from proposals.models import Talk
from proposals.signals import *

from .models import ConversationAboutTalk, ConversationWithParticipant, Message


@receiver(post_save, sender=Participation, dispatch_uid="Create ConversationWithParticipant")
def create_conversation_with_participant(sender, instance, created, **kwargs):
    if not created:
        return
    conversation = ConversationWithParticipant(participation=instance)
    conversation.save()


@receiver(post_save, sender=Talk, dispatch_uid="Create ConversationAboutTalk")
def create_conversation_about_talk(sender, instance, created, **kwargs):
    if not created:
        return
    conversation = ConversationAboutTalk(talk=instance)
    conversation.save()


def check_talk(talk):
    # Subscribe reviewer for these topics to conversations
    reviewers = User.objects.filter(participation__topic__talk=talk)
    talk.conversation.subscribers.add(*reviewers)
    for user in talk.speakers.all():
        participation, created = Participation.on_site.get_or_create(user=user, site=talk.site)
        participation.conversation.subscribers.add(*reviewers)


@receiver(talk_added, dispatch_uid="Notify talk added")
def notify_talk_added(sender, instance, author, **kwargs):
    check_talk(instance)
    message = Message(conversation=instance.conversation, author=author,
                      content='The talk has been proposed.')
    message.save()


@receiver(talk_edited, dispatch_uid="Notify talk edited")
def notify_talk_edited(sender, instance, author, **kwargs):
    check_talk(instance)
    message = Message(conversation=instance.conversation, author=author,
                      content='The talk has been modified.')
    message.save()


@receiver(post_save, sender=Message, dispatch_uid="Notify new message")
def notify_new_message(sender, instance, created, **kwargs):
    if not created:
        # Possibly send a modification notification?
        return
    instance.conversation.new_message(instance)
