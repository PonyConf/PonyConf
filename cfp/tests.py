from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone
from django.contrib import messages

from datetime import datetime, timedelta
from xml.etree import ElementTree as ET
from icalendar import Calendar
import pytz

from .models import *


class VolunteersTests(TestCase):
    def setUp(self):
        site = Site.objects.first()
        conf = site.conference
        conf.name = 'PonyConf'
        conf.save()
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

    def test_enrole_logged_out(self):
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

    def test_enrole_logged_in(self):
        self.client.login(username='a', password='a')
        self.assertRedirects(self.client.get(reverse('volunteer-enrole')), reverse('volunteer-home'))
        self.client.login(username='b', password='b')
        self.assertEqual(self.client.get(reverse('volunteer-enrole')).status_code, 403)
        conf = Conference.objects.first()
        conf.volunteers_opening_date = timezone.now() - timedelta(hours=1)
        conf.save()
        user = User.objects.get(username='b')
        user.first_name = 'Jean'
        user.last_name = 'Mi'
        user.save()
        user.profile.phone_number = '0123456789'
        user.profile.save()
        response = self.client.get(reverse('volunteer-enrole'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Jean Mi"')
        self.assertContains(response, 'value="0123456789"')
        n = Volunteer.objects.count()
        response = self.client.post(reverse('volunteer-enrole'), {'name': 'B'})
        self.assertEqual(Volunteer.objects.count(), n+1)
        v = Volunteer.objects.get(name='B')
        self.assertRedirects(response, reverse('volunteer-home', kwargs=dict(volunteer_token=v.token)),
                             status_code=302, target_status_code=200)
        self.assertRedirects(self.client.get(reverse('volunteer-enrole')), reverse('volunteer-home'))

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

    def test_volunteer_mail_token(self):
        v = Volunteer.objects.get(name='A')
        self.assertEqual(self.client.get(reverse('volunteer-mail-token')).status_code, 200)
        response = self.client.post(reverse('volunteer-mail-token'), {'email': 'notfound@example.org'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(map(lambda m: m.level == messages.ERROR and 'do not know this email' in m.message, response.context['messages'])))
        response = self.client.post(reverse('volunteer-mail-token'), {'email': 'a@example.org'})
        self.assertRedirects(response, reverse('volunteer-mail-token'))

    def test_volunteer_list(self):
        url = reverse('volunteer-list')
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='c', password='c')
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.get(url + '?format=csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="volunteers.csv"')

    def test_volunteer_details(self):
        v = Volunteer.objects.get(name='A')
        url = reverse('volunteer-details', kwargs=dict(volunteer_id=v.pk))
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='c', password='c')
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_activity_list(self):
        url = reverse('activity-list')
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='c', password='c')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_activity_add(self):
        url = reverse('activity-list')
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='c', password='c')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_activity_edit(self):
        conf = Conference.objects.get(name='PonyConf')
        activity = Activity.objects.filter(site=conf.site).first()
        url = reverse('activity-edit', kwargs={'slug': activity.slug})
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='c', password='c')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_activity_remove(self):
        pass


class ProposalTest(TestCase):
    def setUp(self):
        user = User.objects.create_user('jean-mi', email='jean-mi@example.org', password='jean-mi', first_name='Jean', last_name='Mi')
        admin = User.objects.create_user('admin', email='admin@example.org', password='admin', is_superuser=True)
        site = Site.objects.first()
        conf = Conference.objects.get(site=site)
        conf.name = 'PonyConf'
        conf.save()
        category_conf = TalkCategory.objects.create(site=site, name='Conference', label='conference')
        category_ws = TalkCategory.objects.create(site=site, name='Workshop', label='workshop')
        speaker1 = Participant.objects.create(site=site, name='Speaker 1', email='1@example.org')
        speaker2 = Participant.objects.create(site=site, name='Speaker 2', email='2@example.org')
        speaker3 = Participant.objects.create(site=site, name='Speaker 3', email='3@example.org')
        talk1 = Talk.objects.create(site=site, category=category_conf, title='Talk 1', description='This is a 1st talk.')
        talk1.speakers.add(speaker1)
        talk1.speakers.add(speaker2)
        talk2 = Talk.objects.create(site=site, category=category_conf, title='Talk 2', description='This is a 2nd talk.')
        talk2.speakers.add(speaker3)

    def test_home(self):
        self.assertRedirects(self.client.get(reverse('home')), reverse('proposal-home'), status_code=302)
        site = Site.objects.first()
        conf = Conference.objects.get(site=site)
        conf.home = '**Welcome!**'
        conf.save()
        response = self.client.get(reverse('home'))
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, '<strong>Welcome!</strong>')

    def test_opened_categories(self):
        # TODO cover all cases
        conf = Conference.objects.get(name='PonyConf')
        all_categories_pk = TalkCategory.objects.filter(site=conf.site).values_list('pk', flat=True)
        self.assertQuerysetEqual(conf.opened_categories, all_categories_pk, transform=lambda category: category.pk, ordered=False)

    def test_proposal_closed(self):
        conf = Conference.objects.get(name='PonyConf')
        TalkCategory.objects.filter(site=conf.site).all().delete()
        response = self.client.get(reverse('proposal-home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cfp/closed.html')

    def test_proposal_logged_out(self):
        conf = Conference.objects.get(name='PonyConf')
        site = conf.site
        self.assertEqual(self.client.get(reverse('proposal-home')).status_code, 200)
        response = self.client.post(reverse('proposal-home'), {
            'name': 'Jean-Mi',
            'email': 'jean@mi.me',
            'biography': 'I am Jean-Mi!',
            'category': conf.opened_categories.first().pk,
            'title': 'PonyConf',
            'description': 'PonyConf is cool.',
        })
        speaker = Participant.objects.get(site=site, name='Jean-Mi')
        talk = Talk.objects.get(site=site, title='PonyConf')
        self.assertRedirects(response, reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)), 302)
        self.assertTrue(speaker in talk.speakers.all())

    def test_proposal_logged_in(self):
        self.client.login(username='jean-mi', password='jean-mi')
        conf = Conference.objects.get(name='PonyConf')
        site = conf.site
        response = self.client.get(reverse('proposal-home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jean Mi')
        response = self.client.post(reverse('proposal-home'), {
            'name': 'Jean-Mi',
            'biography': 'I am Jean-Mi!',
            'category': conf.opened_categories.first().pk,
            'title': 'PonyConf',
            'description': 'PonyConf is cool.',
        })
        speaker = Participant.objects.get(site=site, name='Jean-Mi')
        self.assertEquals(speaker.email, 'jean-mi@example.org')
        talk = Talk.objects.get(site=site, title='PonyConf')
        self.assertRedirects(response, reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)), 302)
        self.assertTrue(speaker in talk.speakers.all())
        response = self.client.get(reverse('proposal-home'))
        self.assertRedirects(response, reverse('proposal-dashboard'))

    def test_proposal_dashboard(self):
        speaker = Participant.objects.get(name='Speaker 1')
        self.assertEqual(self.client.get(reverse('proposal-dashboard', kwargs=dict(speaker_token=speaker.token))).status_code, 200)

    def test_proposal_profile_edit(self):
        speaker = Participant.objects.get(name='Speaker 1')
        self.assertEqual(self.client.get(reverse('proposal-profile-edit', kwargs=dict(speaker_token=speaker.token))).status_code, 200)

    def test_proposal_talk_details(self):
        speaker1 = Participant.objects.get(name='Speaker 1')
        speaker2 = Participant.objects.get(name='Speaker 2')
        talk1 = Talk.objects.get(title='Talk 1')
        talk2 = Talk.objects.get(title='Talk 2')
        self.assertEqual(self.client.get(reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker1.token, talk_id=talk1.pk))).status_code, 200)
        self.assertEqual(self.client.get(reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker2.token, talk_id=talk1.pk))).status_code, 200)
        self.assertEqual(self.client.get(reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker1.token, talk_id=talk2.pk))).status_code, 404)

    def test_proposal_talk_add(self):
        speaker = Participant.objects.get(name='Speaker 1')
        self.assertEqual(self.client.get(reverse('proposal-talk-add', kwargs=dict(speaker_token=speaker.token))).status_code, 200)

    def test_proposal_talk_edit(self):
        speaker = Participant.objects.get(name='Speaker 1')
        talk = Talk.objects.get(title='Talk 1')
        self.assertEqual(self.client.get(reverse('proposal-talk-edit', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk))).status_code, 200)

    def test_proposal_speaker_add(self):
        speaker = Participant.objects.get(name='Speaker 1')
        talk = Talk.objects.get(title='Talk 1')
        self.assertEqual(self.client.get(reverse('proposal-speaker-add', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk))).status_code, 200)

    def test_proposal_speaker_edit(self):
        speaker = Participant.objects.get(name='Speaker 1')
        co_speaker = Participant.objects.get(name='Speaker 2')
        talk = Talk.objects.get(title='Talk 1')
        self.assertEqual(self.client.get(reverse('proposal-speaker-edit', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk, co_speaker_id=speaker.pk))).status_code, 200)
        self.assertEqual(self.client.get(reverse('proposal-speaker-edit', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk, co_speaker_id=co_speaker.pk))).status_code, 200)

    def test_proposal_speaker_remove(self):
        speaker = Participant.objects.get(name='Speaker 1')
        co_speaker = Participant.objects.get(name='Speaker 2')
        talk = Talk.objects.get(title='Talk 1')
        self.assertEqual(self.client.get(reverse('proposal-speaker-remove', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk, co_speaker_id=speaker.pk))).status_code, 403) 
        self.assertRedirects(
                self.client.get(reverse('proposal-speaker-remove', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk, co_speaker_id=co_speaker.pk))),
                reverse('proposal-talk-details', kwargs=dict(speaker_token=speaker.token, talk_id=talk.pk)),
                status_code=302)

    def test_proposal_mail_token(self):
        p = Participant.objects.get(name='Speaker 1')
        self.assertEqual(self.client.get(reverse('proposal-mail-token')).status_code, 200)
        response = self.client.post(reverse('proposal-mail-token'), {'email': 'notfound@example.org'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(map(lambda m: m.level == messages.ERROR and 'do not know this email' in m.message, response.context['messages'])))
        response = self.client.post(reverse('proposal-mail-token'), {'email': p.email})
        self.assertRedirects(response, reverse('proposal-mail-token'))

    def test_speaker_list(self):
        url = reverse('participant-list')
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Speaker 1')
        self.assertContains(response, 'Speaker 2')
        response = self.client.get(url + '?format=csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="participants.csv"')

    def test_speaker_details(self):
        speaker1 = Participant.objects.get(name='Speaker 1')
        speaker2 = Participant.objects.get(name='Speaker 2')
        url = reverse('participant-details', kwargs={'participant_id': speaker1.token})
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Speaker 1')
        self.assertContains(response, 'Speaker 2')
        self.assertNotContains(response, 'Speaker 3')
        self.assertContains(response, 'Talk 1')
        self.assertNotContains(response, 'Talk 3')

    def test_speaker_edit(self):
        speaker = Participant.objects.get(name='Speaker 1')
        url = reverse('participant-edit', kwargs={'participant_id': speaker.token})
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_speaker_add_talk(self):
        speaker = Participant.objects.get(name='Speaker 1')
        url = reverse('participant-add-talk', kwargs={'participant_id': speaker.pk})
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_talk_list(self):
        url = reverse('talk-list')
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Talk 1')
        response = self.client.get(url + '?format=csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="talks.csv"')

    def test_talk_details(self):
        talk = Talk.objects.get(title='Talk 1')
        url = reverse('talk-details', kwargs=dict(talk_id=talk.token))
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, talk.title)

    def test_talk_speaker_remove(self):
        talk = Talk.objects.get(title='Talk 1')
        count = talk.speakers.count()
        to_remove = talk.speakers.first()
        self.assertTrue(to_remove in talk.speakers.all())
        url = reverse('talk-speaker-remove', kwargs={'talk_id': talk.pk, 'participant_id': to_remove.pk})
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('talk-details', kwargs={'talk_id': talk.token}))
        talk = Talk.objects.get(title='Talk 1')
        self.assertEquals(talk.speakers.count() + 1, count)
        self.assertFalse(to_remove in talk.speakers.all())

    def test_conference(self):
        conf = Conference.objects.get(name='PonyConf')
        url = reverse('conference')
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_category_list(self):
        url = reverse('category-list')
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_category_add(self):
        url = reverse('category-add')
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_tag_list(self):
        url = reverse('tag-list')
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_tag_add(self):
        url = reverse('tag-add')
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)


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
        t3 = Tag.objects.create(site=site, name='Not staff tag', staff=False)
        t3 = Tag.objects.create(site=site, name='Staff tag', staff=True)
        start_date = datetime(year=2000, month=1, day=1, hour=10, tzinfo=pytz.timezone('Europe/Paris'))
        pending_talk = Talk.objects.create(site=site, title='Talk', description='A talk.', category=category)
        pending_talk.speakers.add(participant)
        accepted_talk = Talk.objects.create(site=site, title='Talk', description='A talk.', category=category, room=room, start_date=start_date, duration=60, accepted=True)
        accepted_talk.speakers.add(participant)
        accepted_talk.tags.add(t1)
        accepted_talk.tags.add(t2)
        accepted_talk.tags.add(t3)

    def test_public_schedule(self):
        site = Site.objects.first()
        conf = Conference.objects.get(site=site)
        self.assertEquals(self.client.get(reverse('public-schedule')).status_code, 403)
        conf.schedule_publishing_date = timezone.now() - timedelta(hours=1)
        conf.save()
        self.assertEquals(self.client.get(reverse('public-schedule')).status_code, 200)
        conf.schedule_redirection_url ='http://example.net/schedule.html'
        conf.save()
        self.assertRedirects(self.client.get(reverse('public-schedule')), conf.schedule_redirection_url, status_code=302, fetch_redirect_response=False)

    def test_staff_schedule(self):
        self.assertEqual(self.client.get(reverse('staff-schedule')).status_code, 302)
        self.client.login(username='admin', password='admin')
        self.assertEqual(self.client.get(reverse('staff-schedule')).status_code, 200)

    def test_xml(self):
        self.client.login(username='admin', password='admin')
        response = self.client.get(reverse('staff-schedule') + 'xml/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Public tag')
        self.assertNotContains(response, 'Private tag')
        ET.fromstring(response.content)

    def test_ics(self):
        self.client.login(username='admin', password='admin')
        response = self.client.get(reverse('staff-schedule') + 'ics/')
        self.assertEquals(response.status_code, 200)
        Calendar.from_ical(response.content)

    def test_html(self):
        self.client.login(username='admin', password='admin')
        response = self.client.get(reverse('staff-schedule') + 'html/')
        self.assertContains(response, 'Staff tag')
        self.assertNotContains(response, 'Not staff tag')
        self.assertEquals(response.status_code, 200)

    def test_inexistent_format(self):
        self.client.login(username='admin', password='admin')
        self.assertEquals(self.client.get(reverse('staff-schedule') + 'inexistent/').status_code, 404)
