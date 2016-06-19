from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

from accounts.models import Participation

from .models import ConversationWithParticipant, Message


class ConversationTests(TestCase):
    def setUp(self):
        a, b, c = (User.objects.create_user(guy, email='%s@example.org' % guy, password=guy) for guy in 'abc')
        pa, _ = Participation.objects.get_or_create(user=a, site=Site.objects.first())
        conversation, _ = ConversationWithParticipant.objects.get_or_create(participation=pa)
        Message.objects.create(content='allo', conversation=conversation, author=b)

    def test_models(self):
        self.assertEqual(str(ConversationWithParticipant.objects.first()), 'Conversation with a')
        self.assertEqual(str(Message.objects.first()), 'Message from b')

    def test_views(self):
        url = ConversationWithParticipant.objects.first().get_absolute_url()
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.login(username='c', password='c')
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.get(reverse('correspondents')).status_code, 200)
        self.assertEqual(self.client.get(reverse('inbox')).status_code, 200)
        self.client.post(reverse('inbox'), {'content': 'coucou'})
