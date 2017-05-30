from django.views.generic import FormView, TemplateView
from django.core.urlresolvers import reverse_lazy

from .forms import ProposeForm


class ProposeView(FormView):
    form_class = ProposeForm
    template_name = 'cfp/propose.html'
    success_url = reverse_lazy('propose-complete')


class CompleteView(TemplateView):
    template_name = 'cfp/complete.html'
