from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.timezone import localtime

from datetime import datetime, timedelta
from copy import deepcopy
from collections import OrderedDict, namedtuple
from itertools import islice

from .models import Room

from proposals.models import Talk


Event = namedtuple('Event', ['talk', 'row', 'rowcount'])


class Program:
    def __init__(self, site):
        self.rooms = Room.objects.filter(site=site)
        self.talks = Talk.objects.\
                            filter(site=site, room__in=self.rooms.all(), start_date__isnull=False).\
                            filter(Q(duration__gt=0) | Q(event__duration__gt=0)).\
                            exclude(accepted=False).\
                            order_by('start_date')

        self.timeslots = []
        for talk in self.talks.all():
            duration = talk.estimated_duration()
            assert(duration)
            d1 = talk.start_date
            d2 = d1 + timedelta(minutes=duration)
            if d1 not in self.timeslots:
                self.timeslots.append(d1)
            if d2 not in self.timeslots:
                self.timeslots.append(d2)
        self.timeslots = sorted(self.timeslots)

        self.cols = OrderedDict([(room, 1) for room in self.rooms])
        self.rows = OrderedDict([(timeslot, OrderedDict([(room, []) for room in self.rooms])) for timeslot in self.timeslots[:-1]])

        for talk in self.talks:
            self._add_talk(talk)

    def _add_talk(self, talk):
        room = talk.room
        d1 = self.timeslots.index(talk.start_date)
        d2 = self.timeslots.index(talk.start_date + timedelta(minutes=talk.duration))
        col = None
        for row, timeslot in enumerate(islice(self.timeslots, d1, d2)):
            if col is None:
                col = 0
                while col < len(self.rows[timeslot][room]) and self.rows[timeslot][room][col]:
                    col += 1
                self.cols[room] = max(self.cols[room], col+1)
            event = Event(talk=talk, row=row, rowcount=d2-d1)
            while len(self.rows[timeslot][room]) <= col:
                self.rows[timeslot][room].append(None)
            self.rows[timeslot][room][col] = event

    def _header(self):
        output = '<td>Room</td>'
        room_cell = '<td%(options)s>%(name)s<br><b>%(label)s</b></td>'
        for room, colspan in self.cols.items():
            options = ' colspan="%d"' % colspan
            output += room_cell % {'name': room.name, 'label': room.label, 'options': options}
        return '<tr>%s</tr>' % output

    def _body(self):
        row = '<tr style="%(style)s">%(timeslot)s%(content)s</tr>'
        cell = '<td%(options)s>%(content)s</td>'
        output = []
        for ts, rooms in self.rows.items():
            content = ''
            for room, events in rooms.items():
                for i in range(self.cols[room]):
                    options = ''
                    cellcontent = ''
                    if i < len(events) and events[i]:
                        event = events[i]
                        if event.row != 0:
                            continue
                        options = ' rowspan="%d" bgcolor="%s"' % (event.rowcount, event.talk.event.color)
                        cellcontent = str(event.talk) + ' — ' + event.talk.get_speakers_str()
                    content += cell % {'options': options, 'content': cellcontent}
            style, timeslot = self._timeslot(ts)
            output.append(row % {
                'style': style,
                'timeslot': timeslot,
                'content': content,
            })
        return '\n'.join(output)

    def _timeslot(self, ts):
        template = '<td>%(content)s</td>'
        start = ts
        end = self.timeslots[self.timeslots.index(ts)+1]
        duration = (end - start).seconds / 60
        print(start, end, duration)
        date_to_string = lambda date: datetime.strftime(localtime(date), '%H:%M')
        style = 'height: %dpx;' % int(duration * 0.8)
        timeslot = '<td>%s – %s</td>' % tuple(map(date_to_string, [start, end]))
        return style, timeslot

    def __str__(self):
        template = """<table class="table table-bordered text-center">\n%(header)s\n%(body)s\n</table>"""
        return mark_safe(template % {
            'header': self._header(),
            'body': self._body(),
        })
