from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse

from .utils import markdown_to_html


@login_required
@require_http_methods(["POST"])
def markdown_preview(request):
    content = request.POST.get('data', '')
    return HttpResponse(markdown_to_html(content))
