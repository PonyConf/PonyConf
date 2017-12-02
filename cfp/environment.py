from django.conf import settings

from jinja2.sandbox import SandboxedEnvironment

import pytz


def talk_to_dict(talk):
    return {
        'title': talk.title,
        'description': talk.description,
        'category': str(talk.category),
        'accepted': talk.accepted,
        'confirmed': talk.confirmed,
        'start_date': talk.start_date.astimezone(tz=pytz.timezone(settings.TIME_ZONE)) if talk.start_date else None,
        'duration': talk.estimated_duration,
        'track': str(talk.track) if talk.track else '',
        'video': talk.video,
        'speakers': list(map(speaker_to_dict, talk.speakers.all())),
    }


def speaker_to_dict(speaker):
    return {
        'name': speaker.name,
        'email': speaker.email,
    }


class TalkEnvironment(SandboxedEnvironment):
    def __init__(self, talk, speaker, **options):
        super().__init__(**options)
        self.globals.update({
            'talk': talk_to_dict(talk),
            'speaker': speaker_to_dict(speaker),
        })
