from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from .models import Talk, Topic, Speech


class ProposalsTests(TestCase):
    def setUp(self):
        for guy in 'ab':
            User.objects.create_user(guy, email='%s@example.org' % guy, password=guy)
        Topic.objects.create(name='pipo')

    def test_everything(self):
        # talk-edit
        self.client.login(username='a', password='a')
        self.client.post(reverse('add-talk'), {'title': 'super talk', 'description': 'super', 'event': 1})
        self.assertEqual(str(Talk.on_site.first()), 'super talk')
        self.client.post(reverse('edit-talk', kwargs={'talk': 'super-talk'}),
                         {'title': 'mega talk', 'description': 'mega', 'event': 1})
        self.assertEqual(str(Talk.on_site.first()), 'mega talk')

        # Status Code
        self.client.login(username='a', password='a')
        for view in ['home', 'list-talks', 'add-talk', 'list-topics', 'list-speakers']:
            self.assertEqual(self.client.get(reverse(view)).status_code, 200)
        talk = Talk.on_site.first()
        self.assertEqual(self.client.get(reverse('edit-talk', kwargs={'talk': talk.slug})).status_code, 200)
        self.assertEqual(self.client.get(reverse('show-talk', kwargs={'slug': talk.slug})).status_code, 200)
        self.assertEqual(self.client.get(reverse('list-talks-by-speaker', kwargs={'speaker': 'a'})).status_code, 200)
        self.assertEqual(self.client.get(reverse('show-speaker', kwargs={'username': 'a'})).status_code, 200)

        self.client.login(username='b', password='b')
        self.assertEqual(self.client.post(reverse('edit-talk', kwargs={'talk': 'super-talk'}),
                                          {'title': 'mega talk', 'description': 'mega', 'event': 1}).status_code, 403)
        self.assertEqual(self.client.get(reverse('list-talks')).status_code, 200)

        # Models str & get_asbolute_url
        for model in [Talk, Topic, Speech]:
            item = model.objects.first()
            self.assertEqual(self.client.get(item.get_absolute_url()).status_code, 200)
            self.assertTrue(str(item))
        self.assertEqual(Speech.objects.first().username(), 'a')
