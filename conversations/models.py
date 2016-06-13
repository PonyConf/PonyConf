from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models

from accounts.models import Speaker


class Conversation(models.Model):

    speaker = models.ForeignKey(Speaker, related_name='conversation')
    subscribers = models.ManyToManyField(User, related_name='+')

    def __str__(self):
        return "Conversation with %s" % self.speaker

    def get_absolute_url(self):
        return reverse('show-conversation', kwargs={'conversation': self.pk})


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
