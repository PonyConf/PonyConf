from django.db import models
from django.contrib.auth.models import User

from accounts.models import Participation
from .utils import generate_message_token


class Conversation(models.Model):

    participation = models.OneToOneField(Participation, related_name='conversation')
    subscribers = models.ManyToManyField(User, related_name='+')

    def __str__(self):
        return "Conversation with %s" % self.participation.user


class Message(models.Model):

    conversation = models.ForeignKey(Conversation, related_name='messages')

    token = models.CharField(max_length=64, default=generate_message_token)

    author = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    class Meta:
        ordering = ['date']

    def __str__(self):
        return "Message from %s" % self.author
