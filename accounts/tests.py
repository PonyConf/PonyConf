from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

from .models import Participation, Profile

ROOT_URL = 'accounts'


class AccountTests(TestCase):
    def setUp(self):
        a, b, c = (User.objects.create_user(guy, email='%s@example.org' % guy, password=guy) for guy in 'abc')
        Participation.objects.create(user=a, site=Site.objects.first())
        Participation.objects.create(user=b, site=Site.objects.first())
        Participation.objects.create(user=c, site=Site.objects.first(), orga=True)

    def test_models(self):
        self.assertEqual(Profile.objects.count(), 3)
        self.client.login(username='c', password='c')
        for model in [Profile, Participation]:
            item = model.objects.first()
            self.assertEqual(self.client.get(item.full_link()).status_code, 200)
            self.assertTrue(str(item))

    def test_views(self):
        # User b wants to update its username, email and biography
        user = User.objects.get(username='b')
        self.assertEqual(user.email, 'b@example.org')
        self.assertEqual(user.profile.biography, '')

        self.client.login(username='b', password='b')

        # He tries with an invalid address
        self.client.post(reverse('profile'), {'email': 'bnewdomain.com', 'username': 'z', 'biography': 'tester',
                                              'video_licence': 1})
        self.assertEqual(User.objects.filter(username='z').count(), 0)

        self.client.post(reverse('profile'), {'email': 'b@newdomain.com', 'username': 'z', 'biography': 'tester',
                                              'video_licence': 1})

        user = User.objects.get(username='z')
        self.assertEqual(user.email, 'b@newdomain.com')
        self.assertEqual(user.profile.biography, 'tester')
        self.client.logout()

    def test_participant_views(self):
        self.assertEqual(self.client.get(reverse('registration_register')).status_code, 200)
        self.client.login(username='b', password='b')
        self.assertEqual(self.client.get(reverse('list-participant')).status_code, 403)
        self.assertEqual(self.client.post(reverse('edit-participant', kwargs={'username': 'a'}),
                                          {'biography': 'foo'}).status_code, 403)
        b = User.objects.get(username='b')
        b.is_superuser = True
        b.save()
        p = Participation.objects.get(user=b)
        self.assertFalse(p.orga)
        self.assertEqual(self.client.get(reverse('list-participant')).status_code, 403)
        # login signal should set orga to True due to superuser status
        self.client.login(username='b', password='b')
        p = Participation.objects.get(user=b)
        self.assertTrue(p.orga)
        self.assertEqual(self.client.get(reverse('list-participant')).status_code, 200)
        self.assertEqual(self.client.post(reverse('edit-participant', kwargs={'username': 'a'}),
                                          {'biography': 'foo', 'nootes': 'bar'}).status_code, 200)
        self.assertEqual(User.objects.get(username='a').profile.biography, '')
        self.assertEqual(self.client.post(reverse('edit-participant', kwargs={'username': 'a'}),
                                          {'biography': 'foo', 'notes': 'bar', 'first_name': 'Jules', 'username': 'a',
                                           'last_name': 'César', 'email': 'a@example.org', 'transport': 1,
                                           'connector': 1, 'video_licence': 2, 'constraints': 'nope', 'orga': 0,
                                           }).status_code, 200)
        self.assertEqual(User.objects.get(username='a').profile.biography, 'foo')
        self.assertEqual(Participation.objects.get(user=User.objects.get(username='a')).video_licence, 2)


from datetime import datetime
from .models import AvailabilityTimeslot
class DisponibilitiesTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('a', email='a@example.org', password='a')
        self.participation = Participation.objects.create(user=self.user, site=Site.objects.first())

    def test_is_available(self):
        from django.utils.timezone import is_naive, get_default_timezone
        tz = get_default_timezone()
        d = {}
        for i in range(8, 18, 1):
            d[i] = datetime(2016, 10, 10, i, 0, 0, tzinfo=tz)
        self.assertEquals(self.participation.is_available(d[10]), None)
        AvailabilityTimeslot.objects.create(participation=self.participation, start=d[10], end=d[12])
        self.assertEquals(self.participation.is_available(d[9]), False)
        self.assertEquals(self.participation.is_available(d[11]), True)
        self.assertEquals(self.participation.is_available(d[13]), False)
        self.assertEquals(self.participation.is_available(d[8], d[9]), False)
        self.assertEquals(self.participation.is_available(d[9], d[11]), False)
        self.assertEquals(self.participation.is_available(d[10], d[11]), True)
        self.assertEquals(self.participation.is_available(d[11], d[12]), True)
        self.assertEquals(self.participation.is_available(d[10], d[12]), True)
        self.assertEquals(self.participation.is_available(d[11], d[13]), False)
        self.assertEquals(self.participation.is_available(d[13], d[14]), False)
        AvailabilityTimeslot.objects.create(participation=self.participation, start=d[14], end=d[16])
        self.assertEquals(self.participation.is_available(d[10], d[12]), True)
        self.assertEquals(self.participation.is_available(d[14], d[16]), True)
        self.assertEquals(self.participation.is_available(d[11], d[15]), False)
        self.assertEquals(self.participation.is_available(d[11], d[17]), False)
        self.assertEquals(self.participation.is_available(d[13], d[17]), False)
        self.assertEquals(self.participation.is_available(d[9], d[15]), False)
