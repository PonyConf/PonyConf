from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.timezone import localtime
from django.core.cache import cache
from django.core.urlresolvers import reverse

from datetime import datetime, timedelta
from copy import deepcopy
from collections import OrderedDict, namedtuple
from itertools import islice
from zlib import adler32
import xml.etree.ElementTree as ET

from .models import Conference, Talk, Room


Event = namedtuple('Event', ['talk', 'row', 'rowcount'])


class Program:
    def __init__(self, site, pending=False, cache=True):
        self.site = site
        self.pending = pending
        self.cache = cache
        self.initialized = False

    def _lazy_init(self):
        self.conference = Conference.objects.get(site=self.site)
        self.talks = Talk.objects.\
                            exclude(category__label__exact='').\
                            filter(site=self.site, room__isnull=False, start_date__isnull=False).\
                            filter(Q(duration__gt=0) | Q(category__duration__gt=0))

        if self.pending:
            self.talks = self.talks.exclude(accepted=False)
        else:
            self.talks = self.talks.filter(accepted=True)

        self.talks = self.talks.order_by('start_date')

        self.rooms = Room.objects.filter(talk__in=self.talks.all()).order_by('name').distinct()

        self.days = {}
        for talk in self.talks.all():
            duration = talk.estimated_duration
            assert(duration)
            dt1 = talk.start_date
            d1 = localtime(dt1).date()
            if d1 not in self.days.keys():
                self.days[d1] = {'timeslots': []}
            dt2 = dt1 + timedelta(minutes=duration)
            d2 = localtime(dt2).date()
            if d2 not in self.days.keys():
                self.days[d2] = {'timeslots': []}
            if dt1 not in self.days[d1]['timeslots']:
                self.days[d1]['timeslots'].append(dt1)
            if dt2 not in self.days[d2]['timeslots']:
                self.days[d2]['timeslots'].append(dt2)

        self.cols = OrderedDict([(room, 1) for room in self.rooms])
        for day in self.days.keys():
            self.days[day]['timeslots'] = sorted(self.days[day]['timeslots'])
            self.days[day]['rows'] = OrderedDict([(timeslot, OrderedDict([(room, []) for room in self.rooms])) for timeslot in self.days[day]['timeslots'][:-1]])

        for talk in self.talks.exclude(plenary=True).all():
            self._add_talk(talk)

        for talk in self.talks.filter(plenary=True).all():
            self._add_talk(talk)

        self.initialized = True

    def _add_talk(self, talk):
        room = talk.room
        dt1 = talk.start_date
        d1 = localtime(dt1).date()
        dt2 = talk.start_date + timedelta(minutes=talk.estimated_duration)
        d2 = localtime(dt2).date()
        assert(d1 == d2) # this is a current limitation
        dt1 = self.days[d1]['timeslots'].index(dt1)
        dt2 = self.days[d1]['timeslots'].index(dt2)
        col = None
        for row, timeslot in enumerate(islice(self.days[d1]['timeslots'], dt1, dt2)):
            if col is None:
                col = 0
                while col < len(self.days[d1]['rows'][timeslot][room]) and self.days[d1]['rows'][timeslot][room][col]:
                    col += 1
                self.cols[room] = max(self.cols[room], col+1)
            event = Event(talk=talk, row=row, rowcount=dt2-dt1)
            while len(self.days[d1]['rows'][timeslot][room]) <= col:
                self.days[d1]['rows'][timeslot][room].append(None)
            self.days[d1]['rows'][timeslot][room][col] = event

    def _html_header(self):
        output = '<td>Room</td>'
        room_cell = '<td%(options)s>%(name)s<br><b>%(label)s</b></td>'
        for room, colspan in self.cols.items():
            options = ' style="min-width: 100px;" colspan="%d"' % colspan
            output += room_cell % {'name': escape(room.name), 'label': escape(room.label), 'options': options}
        return '<tr>%s</tr>' % output

    def _html_body(self):
        output = ''
        for day in sorted(self.days.keys()):
            output += self._html_day_header(day)
            output += self._html_day(day)
        return output

    def _html_day_header(self, day):
        row = '<tr><td colspan="%(colcount)s"><h3>%(day)s</h3></td></tr>'
        colcount = 1
        for room, col in self.cols.items():
            colcount += col
        return row % {
            'colcount': colcount,
            'day': datetime.strftime(day, '%A %d %B'),
        }

    def _html_day(self, day):
        output = []
        rows = self.days[day]['rows']
        for ts, rooms in rows.items():
            output.append(self._html_row(day, ts, rooms))
        return '\n'.join(output)

    def _html_row(self, day, ts, rooms):
        row = '<tr style="%(style)s">%(timeslot)s%(content)s</tr>'
        cell = '<td%(options)s>%(content)s</td>'
        content = ''
        for room, events in rooms.items():
            colspan = 1
            for i in range(self.cols[room]):
                options = ' colspan="%d"' % colspan
                cellcontent = ''
                if i < len(events) and events[i]:
                    event = events[i]
                    if event.row != 0:
                        continue
                    options = ' rowspan="%d" bgcolor="%s"' % (event.rowcount, event.talk.category.color)
                    cellcontent = escape(str(event.talk)) + '<br><em>' + escape(event.talk.get_speakers_str()) + '</em>'
                elif (i+1 > len(events) or not events[i+1]) and i+1 < self.cols[room]:
                    colspan += 1
                    continue
                colspan = 1
                content += cell % {'options': options, 'content': mark_safe(cellcontent)}
        style, timeslot = self._html_timeslot(day, ts)
        return row % {
            'style': style,
            'timeslot': timeslot,
            'content': content,
        }

    def _html_timeslot(self, day, ts):
        template = '<td>%(content)s</td>'
        start = ts
        end = self.days[day]['timeslots'][self.days[day]['timeslots'].index(ts)+1]
        duration = (end - start).seconds / 60
        date_to_string = lambda date: datetime.strftime(localtime(date), '%H:%M')
        style = 'height: %dpx;' % int(duration * 1.2)
        timeslot = '<td>%s – %s</td>' % tuple(map(date_to_string, [start, end]))
        return style, timeslot

    def _as_html(self):
        template = """<table class="table table-bordered text-center">\n%(header)s\n%(body)s\n</table>"""
        if not self.initialized:
            self._lazy_init()
        return template % {
            'header': self._html_header(),
            'body': self._html_body(),
        }

    def _as_xml(self):
        if not self.initialized:
            self._lazy_init()
        schedule = ET.Element('schedule')

        #if not len(self.days):
        #    return result % {'conference': '', 'days': ''}

        conference = ET.SubElement(schedule, 'conference')
        elt = ET.SubElement(conference, 'title')
        elt.text = self.site.name
        elt = ET.SubElement(conference, 'venue')
        elt.text = ', '.join(map(lambda x: x.strip(), self.conference.venue.split('\n')))
        elt = ET.SubElement(conference, 'city')
        elt.text = self.conference.city
        elt = ET.SubElement(conference, 'start_date')
        elt.text = sorted(self.days.keys())[0].strftime('%Y-%m-%d')
        elt = ET.SubElement(conference, 'end_date')
        elt.text = sorted(self.days.keys(), reverse=True)[0].strftime('%Y-%m-%d')
        elt = ET.SubElement(conference, 'days_count')
        elt.text = str(len(self.days))

        for index, day in enumerate(sorted(self.days.keys())):
            day_elt = ET.SubElement(schedule, 'day', index=str(index+1), date=day.strftime('%Y-%m-%d'))
            for room in self.rooms.all():
                room_elt = ET.SubElement(day_elt, 'room', name=room.name)
                for talk in self.talks.filter(room=room).order_by('start_date'):
                    if localtime(talk.start_date).date() != day:
                        continue
                    talk_elt = ET.SubElement(day_elt, 'event', id=str(talk.id))
                    duration = talk.estimated_duration
                    persons_elt = ET.SubElement(talk_elt, 'persons')
                    for speaker in talk.speakers.all():
                        person_elt = ET.SubElement(talk_elt, 'person', id=str(speaker.id))
                        person_elt.text = str(speaker)
#                    #if talk.registration_required and self.conference.subscriptions_open:
#                    #    links += mark_safe("""
#                    #    <link tag="registration">%(link)s</link>""" % {
#                    #        'link': reverse('register-for-a-talk', args=[talk.slug]),
#                    #    })
#                    #    registration = """
#                    #  <attendees_max>%(max)s</attendees_max>
#                    #  <attendees_remain>%(remain)s</attendees_remain>""" % {
#                    #    'max': talk.attendees_limit,
#                    #    'remain': talk.remaining_attendees or 0,
#                    #  }
#                    #if talk.materials:
#                    #    links += mark_safe("""
#                    #    <link tag="slides">%(link)s</link>""" % {
#                    #        'link': talk.materials.url,
#                    #    })
#                    #if talk.video:
#                    #    links += mark_safe("""
#                    #    <link tag="video">%(link)s</link>""" % {
#                    #        'link': talk.video,
#                    #    })
                    elt = ET.SubElement(talk_elt, 'start')
                    elt.text = localtime(talk.start_date).strftime('%H:%M')
                    elt = ET.SubElement(talk_elt, 'duration')
                    elt.text = '%02d:%02d' % (talk.estimated_duration / 60, talk.estimated_duration % 60)
                    elt = ET.SubElement(talk_elt, 'room')
                    elt.text = room.name
                    elt = ET.SubElement(talk_elt, 'slug')
                    elt.text = talk.slug
                    elt = ET.SubElement(talk_elt, 'title')
                    elt.text = talk.title
                    elt = ET.SubElement(talk_elt, 'subtitle')
                    elt = ET.SubElement(talk_elt, 'track')
                    elt.text = talk.track or ''
                    elt = ET.SubElement(talk_elt, 'type')
                    elt.text = talk.category.label
                    elt = ET.SubElement(talk_elt, 'language')
                    elt = ET.SubElement(talk_elt, 'description')
                    elt.text = talk.description
                    elt = ET.SubElement(talk_elt, 'links')

        return ET.tostring(schedule)

    def _as_ics(self):
        if not self.initialized:
            self._lazy_init()
        talks = [ICS_TALK.format(site=self.site, talk=talk) for talk in self.talks]
        return ICS_MAIN.format(site=self.site, talks='\n'.join(talks))

    def render(self, output='html'):
        if self.cache:
            cache_entry = 'ponyconf-%d' % adler32('|'.join(map(str, [self.site.domain, output, self.pending])).encode('utf-8'))
            result = cache.get(cache_entry)
            if not result:
                result = getattr(self, '_as_%s' % output)()
                cache.set(cache_entry, result, 3 * 60 * 60) # 3H
            return mark_safe(result)
        else:
            return mark_safe(getattr(self, '_as_%s' % output)())

    def __str__(self):
        return self.render()


# FIXME definitely the wrong place for this, but hey, other templates are already here :P

ICS_MAIN = """BEGIN:VCALENDAR
PRODID:-//{site.domain}//{site.name}//FR
X-WR-CALNAME:PonyConf
X-WR-TIMEZONE:Europe/Paris
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
{talks}
END:VCALENDAR"""

ICS_TALK = """BEGIN:VEVENT
DTSTART:{talk.dtstart}
DTEND:{talk.dtend}
SUMMARY:{talk.title}
LOCATION:{talk.room}
STATUS: CONFIRMED
DESCRIPTION:{talk.description}
UID:{site.domain}/{talk.id}
END:VEVENT
"""
