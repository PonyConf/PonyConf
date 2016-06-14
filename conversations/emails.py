from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
from django.contrib.auth.models import User
from django.core.mail import mail_admins

from .utils import hexdigest_sha256
from .models import Message

import email
import re
from sys import version_info as python_version


@csrf_exempt
@require_http_methods(["POST"])
def email_recv(request):

    if not hasattr(settings, 'REPLY_EMAIL') \
            or not hasattr(settings, 'REPLY_KEY'):
        return HttpResponse(status=501) # Not Implemented

    key = request.POST.get('key')
    if key != settings.REPLY_KEY:
        raise PermissionDenied

    if 'email' not in request.FILES:
        raise HttpResponse(status=400) # Bad Request

    msg = request.FILES['email']
    if python_version < (3,):
        msg = email.message_from_file(msg)
    else:
        msg = email.message_from_bytes(msg.read())

    mfrom = msg.get('From')
    mto = msg.get('To')
    subject = msg.get('Subject')

    if msg.is_multipart():
        msgs = msg.get_payload()
        for m in msgs:
            if m.get_content_type == 'text/plain':
                content = m.get_payload(decode=True)
                break
        else:
            content = msgs[0].get_payload(decode=True)
    else:
        content = msg.get_payload(decode=True)

    if python_version < (3,):
        content = content.decode('utf-8')

    addr = settings.REPLY_EMAIL
    pos = addr.find('@')
    name = addr[:pos]
    domain = addr[pos+1:]

    regexp = '^%s\+(?P<dest>[a-z0-9]{12})(?P<token>[a-z0-9]{60})(?P<key>[a-z0-9]{12})@%s$' % (name, domain)
    p = re.compile(regexp)
    m = None
    for _mto in map(lambda x: x.strip(), mto.split(',')):
        m = p.match(_mto)
        if m:
            break
    if not m: # no one matches
        raise Http404

    author = get_object_or_404(User, profile__email_token=m.group('dest'))
    message = get_object_or_404(Message, token=m.group('token'))
    key = hexdigest_sha256(settings.SECRET_KEY, message.token, author.pk)[0:12]
    if key != m.group('key'):
        raise PermissionDenied

    answer = Message(conversation=message.conversation,
                     author=author, content=content)
    answer.save()

    return HttpResponse()
