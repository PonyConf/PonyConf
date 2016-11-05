import re
import chardet
import logging
from functools import reduce

from email import policy
from email.parser import BytesParser
from email.message import EmailMessage

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Message
from .utils import hexdigest_sha256


@csrf_exempt
@require_http_methods(["POST"])
def email_recv(request):

    if not hasattr(settings, 'REPLY_EMAIL') \
            or not hasattr(settings, 'REPLY_KEY'):
        return HttpResponse(status=501)  # Not Implemented

    key = request.POST.get('key').strip()
    if key != settings.REPLY_KEY:
        raise PermissionDenied

    if 'email' not in request.FILES:
        return HttpResponse(status=400)  # Bad Request

    msg = request.FILES['email']

    msg = BytesParser(policy=policy.default).parsebytes(msg.read())
    body = msg.get_body(preferencelist=('plain',))
    content = body.get_payload(decode=True)

    try:
        content = content.decode(body.get_content_charset())
    except Exception:
        encoding = chardet.detect(content)['encoding']
        content = content.decode(encoding)

    addr = settings.REPLY_EMAIL
    pos = addr.find('@')
    name = addr[:pos]
    domain = addr[pos+1:]

    regexp = '^%s\+(?P<dest>[a-z0-9]{12})(?P<token>[a-z0-9]{60})(?P<key>[a-z0-9]{12})@%s$' % (name, domain)
    p = re.compile(regexp)
    m = None
    addrs = map(lambda x: x.split(',') if x else [], [msg.get('To'), msg.get('Cc')])
    addrs = reduce(lambda x, y: x + y, addrs)
    for _mto in map(lambda x: x.strip(), addrs):
        m = p.match(_mto)
        if m:
            break
    if not m:  # no one matches
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
