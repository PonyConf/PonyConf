import email
import re
from sys import version_info as python_version

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
    if python_version < (3,):
        msg = email.message_from_file(msg)
    else:
        msg = email.message_from_bytes(msg.read())

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
        try:
            content = content.decode('utf-8')
        except DjangoUnicodeDecodeError:
            encoding = chardet.detect(content)['encoding']
            content = content.decode(encoding)

    if content == None:
        content = ""

    addr = settings.REPLY_EMAIL
    pos = addr.find('@')
    name = addr[:pos]
    domain = addr[pos+1:]

    regexp = '^%s\+(?P<dest>[a-z0-9]{12})(?P<token>[a-z0-9]{60})(?P<key>[a-z0-9]{12})@%s$' % (name, domain)
    p = re.compile(regexp)
    m = None
    for _mto in map(lambda x: x.strip(), msg.get('To').split(',')):
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
