from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from datetime import timedelta

from .models import Conference, Volunteer, Activity


class VolunteersTests(TestCase):
    def setUp(self):
        site = Site.objects.first()
        a, b, c = (User.objects.create_user(guy, email='%s@example.org' % guy, password=guy) for guy in 'abc')
        Volunteer.objects.create(site=site, name='A', email=a.email)
        Activity.objects.create(site=site, name='Everythings')
        c.is_superuser = True
        c.save()

    def test_enrollment_is_open(self):
        conf = Conference.objects.first()
        self.assertFalse(conf.volunteers_enrollment_is_open())
        conf.volunteers_opening_date = timezone.now() + timedelta(hours=1)
        self.assertFalse(conf.volunteers_enrollment_is_open())
        conf.volunteers_opening_date = timezone.now() - timedelta(hours=1)
        self.assertTrue(conf.volunteers_enrollment_is_open())
        conf.volunteers_closing_date = timezone.now() - timedelta(hours=1)
        self.assertFalse(conf.volunteers_enrollment_is_open())
        conf.volunteers_closing_date = timezone.now() + timedelta(hours=1)
        self.assertTrue(conf.volunteers_enrollment_is_open())
        conf.volunteers_opening_date = timezone.now() + timedelta(hours=1)
        self.assertFalse(conf.volunteers_enrollment_is_open())
        conf.volunteers_opening_date = None
        self.assertFalse(conf.volunteers_enrollment_is_open())

    def test_enrole(self):
        self.assertEqual(self.client.get(reverse('volunteer-enrole')).status_code, 403)
        conf = Conference.objects.first()
        conf.volunteers_opening_date = timezone.now() - timedelta(hours=1)
        conf.save()
        self.assertEqual(self.client.get(reverse('volunteer-enrole')).status_code, 200)
        n = Volunteer.objects.count()
        response = self.client.post(reverse('volunteer-enrole'), {'name': 'B', 'email': 'b@example.org'})
        self.assertEqual(Volunteer.objects.count(), n+1)
        v = Volunteer.objects.get(name='B')
        self.assertRedirects(response, reverse('volunteer-home', kwargs=dict(volunteer_token=v.token)),
                             status_code=302, target_status_code=200)

    def test_home(self):
        v = Volunteer.objects.get(name='A')
        self.assertEqual(self.client.get(reverse('volunteer-home', kwargs=dict(volunteer_token=v.token))).status_code, 200)

    def test_update_activity(self):
        v = Volunteer.objects.get(name='A')
        a = Activity.objects.get(name='Everythings')
        self.assertEqual(self.client.get(reverse('volunteer-join', kwargs=dict(volunteer_token=v.token, activity=a.pk))).status_code, 404)
        conf = Conference.objects.first()
        conf.volunteers_opening_date = timezone.now() - timedelta(hours=1)
        conf.save()
        self.assertRedirects(self.client.get(reverse('volunteer-join', kwargs=dict(volunteer_token=v.token, activity=a.slug))),
                             reverse('volunteer-home', kwargs=dict(volunteer_token=v.token)), status_code=302, target_status_code=200)
        self.assertRedirects(self.client.get(reverse('volunteer-quit', kwargs=dict(volunteer_token=v.token, activity=a.slug))),
                             reverse('volunteer-home', kwargs=dict(volunteer_token=v.token)), status_code=302, target_status_code=200)
