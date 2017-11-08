from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from datetime import datetime, timedelta
from xml.etree import ElementTree as ET
import pytz

from .models import *


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


class ProposalTest(TestCase):
    def setUp(self):
        site = Site.objects.first()
        conf = Conference.objects.get(site=site)
        conf.name = 'PonyConf'
        conf.save()
        category_conf = TalkCategory.objects.create(site=site, name='Conference', label='conference')
        category_ws = TalkCategory.objects.create(site=site, name='Workshop', label='workshop')
        speaker1 = Participant.objects.create(site=site, name='Speaker 1', email='1@example.org')
        speaker2 = Participant.objects.create(site=site, name='Speaker 2', email='2@example.org')
        talk = Talk.objects.create(site=site, category=category_conf, title='Talk', description='This is a talk.')
        talk.speakers.add(speaker1)
        talk.speakers.add(speaker2)

    def test_opened_categories(self):
        # TODO cover all cases
        conf = Conference.objects.get(name='PonyConf')
        all_categories_pk = TalkCategory.objects.filter(site=conf.site).values_list('pk', flat=True)
        self.assertQuerysetEqual(conf.opened_categories, all_categories_pk, transform=lambda category: category.pk, ordered=False)

    def test_proposal_home(self):
        self.assertEqual(self.client.get(reverse('proposal-home')).status_code, 200)

    def test_proposal_dashboard(self):
        speaker = Participant.objects.get(name='Speaker 1')
        self.assertEqual(self.client.get(reverse('proposal-dashboard', kwargs=dict(speaker_token=speaker.token))).status_code, 200)

    def test_proposal_profile_edit(self):
        speaker = Participant.objects.get(name='Speaker 1')
        self.assertEqual(self.client.get(reverse('proposal-profile-edit', kwargs=dict(speaker_token=speaker.token))).status_code, 200)

    def test_proposal_talk_details(self):
        speaker = Participant.objects.get(name='Speaker 1')
        talk = Talk.objects.get(title='Talk')
        self.assertEqual(self.client.get(reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk))).status_code, 200)

    def test_proposal_talk_edit(self):
        speaker = Participant.objects.get(name='Speaker 1')
        talk = Talk.objects.get(title='Talk')
        self.assertEqual(self.client.get(reverse('proposal-talk-edit', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk))).status_code, 200)

    def test_proposal_speaker_add(self):
        speaker = Participant.objects.get(name='Speaker 1')
        talk = Talk.objects.get(title='Talk')
        self.assertEqual(self.client.get(reverse('proposal-speaker-add', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk))).status_code, 200)

    def test_proposal_speaker_edit(self):
        speaker = Participant.objects.get(name='Speaker 1')
        co_speaker = Participant.objects.get(name='Speaker 2')
        talk = Talk.objects.get(title='Talk')
        self.assertEqual(self.client.get(reverse('proposal-speaker-edit', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk, co_speaker_id=speaker.pk))).status_code, 200)
        self.assertEqual(self.client.get(reverse('proposal-speaker-edit', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk, co_speaker_id=co_speaker.pk))).status_code, 200)

    def test_proposal_speaker_remove(self):
        speaker = Participant.objects.get(name='Speaker 1')
        co_speaker = Participant.objects.get(name='Speaker 2')
        talk = Talk.objects.get(title='Talk')
        self.assertEqual(self.client.get(reverse('proposal-speaker-remove', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk, co_speaker_id=speaker.pk))).status_code, 403) 
        self.assertRedirects(
                self.client.get(reverse('proposal-speaker-remove', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk, co_speaker_id=co_speaker.pk))),
                reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)),
                status_code=302)


class ScheduleTest(TestCase):
    def setUp(self):
        site = Site.objects.first()
        conf = Conference.objects.get(site=site)
        user = User.objects.create_user('user', email='user@example.org', password='user')
        admin = User.objects.create_user('admin', email='admin@example.org', password='admin', is_superuser=True)
        room = Room.objects.create(site=site, name='Room 1')
        category = TalkCategory.objects.create(site=site, name='Conference', label='conference')
        participant = Participant.objects.create(site=site, name='Participant 1', email='1@example.org')
        t1 = Tag.objects.create(site=site, name='Private tag', public=False)
        t2 = Tag.objects.create(site=site, name='Public tag', public=True)
        start_date = datetime(year=2000, month=1, day=1, hour=10, tzinfo=pytz.timezone('Europe/Paris'))
        pending_talk = Talk.objects.create(site=site, title='Talk', description='A talk.', category=category)
        pending_talk.speakers.add(participant)
        accepted_talk = Talk.objects.create(site=site, title='Talk', description='A talk.', category=category, room=room, start_date=start_date, duration=60, accepted=True)
        accepted_talk.speakers.add(participant)
        accepted_talk.tags.add(t1)
        accepted_talk.tags.add(t2)

    def test_xml(self):
        self.assertEqual(self.client.get(reverse('staff-schedule') + 'xml/').status_code, 302)
        self.client.login(username='admin', password='admin')
        response = self.client.get(reverse('staff-schedule') + 'xml/')
        self.assertContains(response, 'Public tag')
        self.assertNotContains(response, 'Private tag')
        ET.fromstring(response.content)
