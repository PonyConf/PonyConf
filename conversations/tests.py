from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.core import mail
from django.conf import settings

from accounts.models import Participation
from proposals.models import Topic, Talk, Event

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
        site = Site.objects.first()
        Talk.objects.get_or_create(site=site, proposer=a, title='a talk', description='yay', event=Event.objects.get(site=site, name='other'))

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


@override_settings(DEFAULT_FROM_EMAIL='noreply@example.org',
                   REPLY_EMAIL='reply@example.org',
                   REPLY_KEY='secret')
class EmailTests(TestCase):
    def setUp(self):
        for guy in 'abcd':
            setattr(self, guy, User.objects.create_user(guy, email='%s@example.org' % guy, password=guy))
        a_p = Participation(user=self.a, site=Site.objects.first())
        a_p.orga = True
        a_p.save()
        t = Topic(name='Topic 1', site=Site.objects.first())
        t.save()
        t.reviewers.add(self.b)


    def test_talk_notification(self):
        self.client.login(username='c', password='c')
        # Check that login create participation
        self.assertTrue(Participation.objects.filter(user=self.c, site=Site.objects.first()).exists())
        # Propose new talk
        topic = Topic.objects.get(name='Topic 1')
        response = self.client.post(reverse('add-talk'), {
            'title': 'Talk 1',
            'description': 'This is the first talk',
            'topics': (topic.pk,),
            'event': 1,
            'speakers': (self.c.pk, self.d.pk),
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Talk proposed') # check messages notification
        talk = Talk.objects.get(site=Site.objects.first(), title='Talk 1')
        conv = ConversationAboutTalk.objects.get(talk=talk)
        # Orga and reviewer should have been subscribed to the conversation about the talk
        self.assertEqual(set([self.a, self.b]), set(conv.subscribers.all()))
        # Both should have received an email notification
        self.assertEqual(len(mail.outbox), 2)
        for m in mail.outbox:
            self.assertEqual(m.from_email, '%s <%s>' % (self.c.profile, settings.DEFAULT_FROM_EMAIL))
            self.assertTrue('Talk: %s' % talk.title)
            self.assertTrue(len(m.to), 1)
            self.assertTrue(m.to[0] in [ self.a.email, self.b.email ])
        # Both should have been subscribed to conversations with each speakers
        for user in [self.c, self.d]:
            # Participation should have been created as the user is a speaker
            p = Participation.objects.get(user=user, site=Site.objects.first())
            conv = ConversationWithParticipant.objects.get(participation=p)
            self.assertEqual(set([self.a, self.b]), set(conv.subscribers.all()))
