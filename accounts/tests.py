from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

from .models import Profile, Speaker

ROOT_URL = 'accounts'


class AccountTests(TestCase):
    def setUp(self):
        for guy in 'ab':
            User.objects.create_user(guy, email='%s@example.org' % guy, password=guy)
        Speaker.objects.create(user=User.objects.first(), site=Site.objects.first())

    def test_models(self):
        self.assertEqual(Profile.objects.count(), 2)
        self.client.login(username='b', password='b')
        for model in [Profile, Speaker]:
            item = model.objects.first()
            self.assertEqual(self.client.get(item.get_absolute_url()).status_code, 200)
            self.assertTrue(str(item))

    def test_views(self):
        # User b wants to update its username, email and biography
        user = User.objects.get(username='b')
        self.assertEqual(user.email, 'b@example.org')
        self.assertEqual(user.profile.biography, '')

        self.client.login(username='b', password='b')

        # He tries with an invalid address
        self.client.post(reverse('profile'), {'email': 'bnewdomain.com', 'username': 'z', 'biography': 'tester'})
        self.assertEqual(User.objects.filter(username='z').count(), 0)

        self.client.post(reverse('profile'), {'email': 'b@newdomain.com', 'username': 'z', 'biography': 'tester'})

        user = User.objects.get(username='z')
        self.assertEqual(user.email, 'b@newdomain.com')
        self.assertEqual(user.profile.biography, 'tester')
        self.client.logout()
