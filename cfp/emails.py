from django.utils.translation import ugettext as _
from django.utils.html import escape

from pprint import pformat
from textwrap import indent

from mailing.utils import send_message
from .environment import TalkEnvironment


def talk_email_render_preview(talk, speaker, subject, body):
    env = TalkEnvironment(talk, speaker)
    try:
        subject = env.from_string(subject).render()
    except Exception:
        return _('There is an error in your subject template.')
    try:
        body = env.from_string(body).render()
    except Exception:
        return _('There is an error in your body template.')
    context = {'talk': env.globals['talk'], 'speaker': env.globals['speaker']}
    preview = '<b>' + _('Environment:') + '</b>\n\n' + escape(indent(pformat(context, indent='2'), '  '))
    preview += '\n\n<b>' + _('Subject:') + '</b> ' + escape(subject) + '\n<b>' + _('Body:') + '</b>\n' + escape(body)
    return preview


def talk_email_send(talks, subject, body):
    sent = 0
    for talk in talks.all():
        for speaker in talk.speakers.all():
            env = TalkEnvironment(talk, speaker)
            s = env.from_string(subject).render()
            c = env.from_string(body).render()
            send_message(speaker.conversation, talk.site.conference, subject=s, content=c)
            sent += 1
    return sent
