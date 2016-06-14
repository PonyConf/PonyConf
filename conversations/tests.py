from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase

from accounts.models import Participation

from .models import Conversation, Message
from .utils import get_reply_addr


class ConversationTests(TestCase):
    def setUp(self):
        a, b = (User.objects.create_user(guy, email='%s@example.org' % guy, password=guy) for guy in 'ab')
        participation = Participation.objects.create(user=a, site=Site.objects.first())
        conversation = Conversation.objects.create(speaker=speaker)
        Message.objects.create(token='pipo', conversation=conversation, author=a, content='allo')

    def test_models(self):
        self.assertEqual(str(Conversation.objects.first()), 'Conversation with a')
        self.assertEqual(str(Message.objects.first()), 'Message from a')

    def test_views(self):
        self.assertEqual(self.client.get(Conversation.objects.first().get_absolute_url()).status_code, 200)

    def test_utils(self):
        ret = ['pipo+         11183704aabfddb3d694ff4f24c0daadfa2d8d2193336e345f92a6fd3ffb6a19e7@example.org']
        self.assertEqual(get_reply_addr(1, User.objects.first()), ret)
