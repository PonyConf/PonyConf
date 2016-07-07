from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models

from accounts.models import Participation
from ponyconf.utils import PonyConfModel
from proposals.models import Talk

from .utils import generate_message_token, notify_by_email


class Message(PonyConfModel):

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    conversation = GenericForeignKey('content_type', 'object_id')

    token = models.CharField(max_length=64, default=generate_message_token, unique=True)

    author = models.ForeignKey(User)
    content = models.TextField()
    system = models.BooleanField(default=False)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return "Message from %s" % self.author

    def get_absolute_url(self):
        return self.conversation.get_absolute_url()


class Conversation(PonyConfModel):

    subscribers = models.ManyToManyField(User, related_name='+', blank=True)

    class Meta:
        abstract = True


class ConversationWithParticipant(Conversation):

    participation = models.OneToOneField(Participation, related_name='conversation')
    messages = GenericRelation(Message)

    uri = 'inbox'
    template = 'participant_message'

    def __str__(self):
        return "Conversation with %s" % self.participation.user

    def get_absolute_url(self):
        return reverse('conversation', kwargs={'username': self.participation.user.username})

    def get_site(self):
        return self.participation.site

    def new_message(self, message):
        site = self.get_site()
        subject = '[%s] Conversation with %s' % (site.name, self.participation.user.profile)
        recipients = list(self.subscribers.all())
        # Auto-subscribe
        if message.author != self.participation.user and message.author not in recipients:
            self.subscribers.add(message.author)
        data = {
            'content': message.content,
            'uri': site.domain + reverse('conversation', args=[self.participation.user.username]),
        }
        first = self.messages.first()
        if first != message:
            ref = first.token
        else:
            ref = None
        notify_by_email('message', data, subject, message.author, recipients, message.token, ref)

        if message.author != self.participation.user:
            subject = '[%s] Message notification' % site.name
            data.update({
                'uri': site.domain + reverse('inbox')
            })
            notify_by_email('message', data, subject, message.author, [self.participation.user], message.token, ref)


class ConversationAboutTalk(Conversation):

    talk = models.OneToOneField(Talk, related_name='conversation')
    messages = GenericRelation(Message)

    uri = 'inbox'
    template = 'talk_message'

    def __str__(self):
        return "Conversation about %s" % self.talk.title

    def get_absolute_url(self):
        return self.talk.get_absolute_url()

    def get_site(self):
        return self.talk.site

    def new_message(self, message):
        site = self.get_site()
        first = self.messages.first()
        if not message.system and message.author not in self.subscribers.all():
            self.subscribers.add(message.author)
        recipients = self.subscribers.all()
        data = {
            'uri': site.domain + reverse('show-talk', args=[self.talk.slug]),
        }
        if first == message:
            subject = '[%s] Talk: %s' % (site.name, self.talk.title)
            template = 'talk_notification'
            ref = None
            data.update({
                'talk': self.talk,
                'proposer': message.author,
                'proposer_uri': site.domain + reverse('show-speaker', args=[message.author.username])
            })
        else:
            subject = 'Re: [%s] Talk: %s' % (site.name, self.talk.title)
            template = 'message'
            ref = first.token
            data.update({'content': message.content})
        notify_by_email(template, data, subject, message.author, recipients, message.token, ref)
