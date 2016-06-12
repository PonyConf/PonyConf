from django.db import models
from django.contrib.auth.models import User

from accounts.models import Speaker


class Conversation(models.Model):

    speaker = models.ForeignKey(Speaker, related_name='conversation')
    subscribers = models.ManyToManyField(User, related_name='+')

    def __str__(self):
        return "Conversation with %s" % self.speaker


class Message(models.Model):

    token = models.CharField(max_length=64)
    conversation = models.ForeignKey(Conversation, related_name='messages')

    author = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    class Meta:
        ordering = ['date']

    def __str__(self):
        return "Message from %s" % self.author
