from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from accounts.models import PonyConfSpeaker
from .models import Topic, Talk, Speach


class ProposalsTests(TestCase):
    def setUp(self):
        for guy in 'ab':
            User.objects.create_user(guy, email='%s@example.org' % guy, password=guy)

    def test_views(self):
        # talk-edit
        self.client.login(username='a', password='a')
        self.client.post(reverse('add-talk'), {'title': 'super talk', 'description': 'super'})
        self.assertEqual(str(Talk.on_site.first()), 'super talk')
        self.client.post(reverse('edit-talk', kwargs={'talk': 'super-talk'}),
                         {'title': 'mega talk', 'description': 'mega'})
        self.assertEqual(str(Talk.on_site.first()), 'mega talk')

        # Status Code
        self.client.login(username='a', password='a')
        for view in ['home', 'list-talks', 'add-talk', 'list-topics', 'list-speakers']:
            self.assertEqual(self.client.get(reverse(view)).status_code, 200)
        talk = Talk.on_site.first()
        for view in ['edit-talk', 'show-talk']:
            self.assertEqual(self.client.get(reverse(view, kwargs={'talk': talk.slug})).status_code, 200)
        self.assertEqual(self.client.get(reverse('list-talks-by-speaker', kwargs={'speaker': 'a'})).status_code, 200)
        self.assertEqual(self.client.get(reverse('show-user', kwargs={'username': 'a'})).status_code, 200)


        self.client.login(username='b', password='b')
        self.assertEqual(self.client.post(reverse('edit-talk', kwargs={'talk': 'super-talk'}),
                                          {'title': 'mega talk', 'description': 'mega'}).status_code, 403)
        self.assertEqual(self.client.get(reverse('list-talks')).status_code, 200)
