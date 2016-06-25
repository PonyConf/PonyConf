from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

from accounts.models import Participation
from proposals.models import Talk

from .models import ConversationAboutTalk, ConversationWithParticipant, Message


class ConversationTests(TestCase):
    def setUp(self):
        a, b, c, d = (User.objects.create_user(guy, email='%s@example.org' % guy, password=guy) for guy in 'abcd')
        d.is_superuser = True
        d.save()
        pa, _ = Participation.objects.get_or_create(user=a, site=Site.objects.first())
        conversation, _ = ConversationWithParticipant.objects.get_or_create(participation=pa)
        Message.objects.create(content='allo', conversation=conversation, author=b)
        Message.objects.create(content='aluil', conversation=conversation, author=a)
        Talk.objects.get_or_create(site=Site.objects.first(), proposer=a, title='a talk', description='yay')

    def test_models(self):
        talk, participant, message = (model.objects.first() for model in
                                      (ConversationAboutTalk, ConversationWithParticipant, Message))
        self.assertEqual(str(talk), 'Conversation about a talk')
        self.assertEqual(str(participant), 'Conversation with a')
        self.assertEqual(str(message), 'Message from b')
        self.assertEqual(message.get_absolute_url(), '/conversations/with/a/')
        self.assertEqual(talk.get_absolute_url(), '/talk/details/a-talk')

    def test_views(self):
        url = ConversationWithParticipant.objects.first().get_absolute_url()
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.login(username='c', password='c')
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.get(reverse('correspondents')).status_code, 200)
        self.assertEqual(self.client.get(reverse('inbox')).status_code, 200)
        self.client.post(reverse('inbox'), {'content': 'coucou'})
        self.client.login(username='d', password='d')
        self.client.post(url, {'content': 'im superuser'})
        self.assertEqual(Message.objects.last().content, 'im superuser')
