from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.timezone import localtime

from datetime import datetime, timedelta
from copy import deepcopy
from collections import OrderedDict, namedtuple
from itertools import islice

from .models import Room

from proposals.models import Conference, Talk


Event = namedtuple('Event', ['talk', 'row', 'rowcount'])


class Program:
    def __init__(self, site, empty_rooms=False, talk_filter=None):
        self.site = site
        self.talks = Talk.objects.\
                            filter(site=site, room__isnull=False, start_date__isnull=False).\
                            filter(Q(duration__gt=0) | Q(event__duration__gt=0)).\
                            exclude(accepted=False).\
                            order_by('start_date')

        if talk_filter:
            self.talks = self.talks.filter(talk_filter)

        if empty_rooms:
            self.rooms = Room.objects.filter(site=site)
        else:
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

    def _header(self):
        output = '<td>Room</td>'
        room_cell = '<td%(options)s>%(name)s<br><b>%(label)s</b></td>'
        for room, colspan in self.cols.items():
            options = ' style="min-width: 100px;" colspan="%d"' % colspan
            output += room_cell % {'name': escape(room.name), 'label': escape(room.label), 'options': options}
        return '<tr>%s</tr>' % output

    def _body(self):
        output = ''
        for day in sorted(self.days.keys()):
            output += self._day_header(day)
            output += self._day(day)
        return output

    def _day_header(self, day):
        row = '<tr><td colspan="%(colcount)s"><h3>%(day)s</h3></td></tr>'
        colcount = 1
        for room, col in self.cols.items():
            colcount += col
        return row % {
            'colcount': colcount,
            'day': datetime.strftime(day, '%A %d %B'),
        }

    def _day(self, day):
        output = []
        rows = self.days[day]['rows']
        for ts, rooms in rows.items():
            output.append(self._row(day, ts, rooms))
        return '\n'.join(output)

    def _row(self, day, ts, rooms):
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
                    options = ' rowspan="%d" bgcolor="%s"' % (event.rowcount, event.talk.event.color)
                    cellcontent = escape(str(event.talk)) + '<br><em>' + escape(event.talk.get_speakers_str()) + '</em>'
                elif (i+1 > len(events) or not events[i+1]) and i+1 < self.cols[room]:
                    colspan += 1
                    continue
                colspan = 1
                content += cell % {'options': options, 'content': mark_safe(cellcontent)}
        style, timeslot = self._timeslot(day, ts)
        return row % {
            'style': style,
            'timeslot': timeslot,
            'content': content,
        }

    def _timeslot(self, day, ts):
        template = '<td>%(content)s</td>'
        start = ts
        end = self.days[day]['timeslots'][self.days[day]['timeslots'].index(ts)+1]
        duration = (end - start).seconds / 60
        date_to_string = lambda date: datetime.strftime(localtime(date), '%H:%M')
        style = 'height: %dpx;' % int(duration * 1.2)
        timeslot = '<td>%s – %s</td>' % tuple(map(date_to_string, [start, end]))
        return style, timeslot

    def as_html(self):
        template = """<table class="table table-bordered text-center">\n%(header)s\n%(body)s\n</table>"""

        self.cols = OrderedDict([(room, 1) for room in self.rooms])
        for day in self.days.keys():
            self.days[day]['timeslots'] = sorted(self.days[day]['timeslots'])
            self.days[day]['rows'] = OrderedDict([(timeslot, OrderedDict([(room, []) for room in self.rooms])) for timeslot in self.days[day]['timeslots'][:-1]])

        for talk in self.talks.exclude(plenary=True).all():
            self._add_talk(talk)

        for talk in self.talks.filter(plenary=True).all():
            self._add_talk(talk)

        return mark_safe(template % {
            'header': self._header(),
            'body': self._body(),
        })

    def as_xml(self):
        result = """<?xml version="1.0" encoding="UTF-8"?>
<schedule>
%(conference)s
%(days)s
</schedule>
"""

        if not len(self.days):
            return result % {'conference': '', 'days': ''}

        conference = Conference.objects.get(site=self.site)
        conference_xml = """<conference>
  <title>%(title)s</title>
  <subtitle></subtitle>
  <venue>%(venue)s</venue>
  <city>%(city)s</city>
  <start>%(start_date)s</start>
  <end>%(end_date)s</end>
  <days>%(days_count)s</days>
  <day_change>09:00:00</day_change>
  <timeslot_duration>00:05:00</timeslot_duration>
</conference>
""" % {
            'title': self.site.name,
            'venue': ', '.join(map(lambda x: x.strip(), conference.venue.split('\n'))),
            'city': conference.city,
            'start_date': sorted(self.days.keys())[0].strftime('%Y-%m-%d'),
            'end_date': sorted(self.days.keys(), reverse=True)[0].strftime('%Y-%m-%d'),
            'days_count': len(self.days),
        }

        days_xml = ''
        for index, day in enumerate(sorted(self.days.keys())):
            days_xml += '<day index="%(index)s" date="%(date)s">\n' % {
                'index': index + 1,
                'date': day.strftime('%Y-%m-%d'),
            }
            for room in self.rooms.all():
                days_xml += '  <room name="%s">\n' % room.name
                for talk in self.talks.filter(room=room).order_by('start_date'):
                    if localtime(talk.start_date).date() != day:
                        continue
                    duration = talk.estimated_duration
                    persons = ''
                    for speaker in talk.speakers.all():
                        persons += '          <person id="%(person_id)s">%(person)s</person>\n' % {
                            'person_id': speaker.id,
                            'person': str(speaker),
                        }
                    days_xml += """    <event id="%(id)s">
        <start>%(start)s</start>
        <duration>%(duration)s</duration>
        <room>%(room)s</room>
        <slug>%(slug)s</slug>
        <title>%(title)s</title>
        <subtitle/>
        <track>%(track)s</track>
        <type>%(type)s</type>
        <language/>
        <abstract>%(abstract)s</abstract>
        <description>%(description)s</description>
        <persons>
%(persons)s        </persons>
        <links>
        </links>
      </event>\n""" % {
                        'id': talk.id,
                        'start': localtime(talk.start_date).strftime('%H:%M'),
                        'duration': '%02d:%02d' % (talk.estimated_duration / 60, talk.estimated_duration % 60),
                        'room': escape(room.name),
                        'slug': escape(talk.slug),
                        'title': escape(talk.title),
                        'track': escape(talk.track),
                        'type': escape(talk.event.name),
                        'abstract': escape(talk.abstract),
                        'description': escape(talk.description),
                        'persons': persons,
                    }
                days_xml += '  </room>\n'
            days_xml += '</day>\n'

        return result % {
            'conference': '\n'.join(map(lambda x: '  ' + x, conference_xml.split('\n'))),
            'days': '\n'.join(map(lambda x: '  ' + x, days_xml.split('\n'))),
        }

    def __str__(self):
        return self.as_html()
