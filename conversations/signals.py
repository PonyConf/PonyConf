from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Participation
from proposals.models import Talk
from proposals.signals import new_talk

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


@receiver(new_talk, dispatch_uid="Notify new talk")
def notify_new_talk(sender, instance, **kwargs):
    # Subscribe reviewer for these topics to conversations
    reviewers = User.objects.filter(participation__topic__talk=instance)
    instance.conversation.subscribers.add(*reviewers)
    for user in instance.speakers.all():
        participation = Participation.on_site.get(user=user)
        participation.conversation.subscribers.add(*reviewers)
    # Notification of this new talk
    message = Message(conversation=instance.conversation, author=instance.proposer,
                      content='The talk has been proposed.')
    message.save()


@receiver(post_save, sender=Message, dispatch_uid="Notify new message")
def notify_new_message(sender, instance, created, **kwargs):
    if not created:
        # Possibly send a modification notification?
        return
    instance.conversation.new_message(instance)
