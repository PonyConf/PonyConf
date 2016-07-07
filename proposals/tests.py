from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.sites.models import Site

from accounts.models import Participation

from .models import Talk, Topic, Vote


class ProposalsTests(TestCase):
    def setUp(self):
        a, b, c = (User.objects.create_user(guy, email='%s@example.org' % guy, password=guy) for guy in 'abc')
        Topic.objects.create(name='topipo', site=Site.objects.first())
        c.is_superuser = True
        c.save()

    def test_everything(self):
        # talk-edit
        self.client.login(username='a', password='a')
        self.client.post(reverse('add-talk'), {'title': 'super talk', 'description': 'super', 'event': 1, 'topics': 1,
                                               'speakers': 1})
        talk = Talk.on_site.first()
        self.assertEqual(str(talk), 'super talk')
        self.assertEqual(talk.description, 'super')
        self.client.post(reverse('edit-talk', kwargs={'talk': 'super-talk'}),
                         {'title': 'mega talk', 'description': 'mega', 'event': 1, 'speakers': 1})
        self.assertEqual(str(talk), 'super talk')  # title is read only there
        talk = Talk.on_site.first()
        self.assertEqual(talk.description, 'mega')

        # Status Code
        for view in ['home', 'list-talks', 'add-talk', 'list-topics', 'list-speakers']:
            self.assertEqual(self.client.get(reverse(view)).status_code, 302 if view == 'list-speakers' else 200)
        self.assertEqual(self.client.get(reverse('edit-talk', kwargs={'talk': talk.slug})).status_code, 200)
        self.assertEqual(self.client.get(reverse('show-talk', kwargs={'slug': talk.slug})).status_code, 200)
        self.assertEqual(self.client.get(reverse('show-speaker', kwargs={'username': 'a'})).status_code, 200)

        self.client.login(username='b', password='b')
        self.assertEqual(self.client.post(reverse('edit-talk', kwargs={'talk': 'super-talk'}),
                                          {'title': 'mega talk', 'description': 'mega', 'event': 1}).status_code, 403)
        self.assertEqual(self.client.get(reverse('list-talks')).status_code, 200)

        # Vote
        self.assertEqual(talk.score(), 0)
        self.assertEqual(self.client.get(reverse('vote', kwargs={'talk': talk.slug, 'score': 2})).status_code, 403)
        self.client.login(username='c', password='c')
        self.assertEqual(self.client.get(reverse('vote', kwargs={'talk': talk.slug, 'score': 2})).status_code, 302)
        self.assertEqual(talk.score(), 2)

        # Models str & get_asbolute_url
        for model in [Talk, Topic, Vote]:
            item = model.objects.first()
            self.assertEqual(self.client.get(item.get_absolute_url()).status_code, 200)
            self.assertTrue(str(item))

        # Talk.is_{editable,moderable}_by
        a, b, c = User.objects.all()
        self.assertTrue(talk.is_moderable_by(c))
        self.assertFalse(talk.is_editable_by(b))
        self.assertFalse(talk.is_moderable_by(b))
        self.client.login(username='a', password='a')
        self.client.post(reverse('edit-talk', kwargs={'talk': 'super-talk'}),
                         {'title': 'mega talk', 'description': 'mega', 'event': 1, 'speakers': "2,1"})
        self.assertTrue(talk.is_editable_by(b))
        self.assertFalse(talk.is_moderable_by(b))

        # Only orga can edit topics
        self.client.login(username='b', password='b')
        self.assertFalse(Participation.on_site.get(user=b).orga)
        self.assertEqual(self.client.get(reverse('edit-topic', kwargs={'slug': 'topipo'})).status_code, 302)
        Participation.on_site.filter(user=b).update(orga=True)
        self.assertEqual(self.client.get(reverse('edit-topic', kwargs={'slug': 'topipo'})).status_code, 302)
        self.client.login(username='c', password='c') # superuser
        self.assertEqual(self.client.get(reverse('edit-topic', kwargs={'slug': 'topipo'})).status_code, 200)
        self.assertEqual(self.client.get(reverse('list-topics')).status_code, 200)
