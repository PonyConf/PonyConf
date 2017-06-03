from django.views.generic import FormView, TemplateView
from django.core.urlresolvers import reverse_lazy

from .forms import ProposeForm


class ProposeView(FormView):
    form_class = ProposeForm
    template_name = 'cfp/propose.html'
    success_url = reverse_lazy('propose-complete')

def propose(request):
    TalkForm = modelform_factory(Talk)
    ParticipantForm = modelform_factory(Participant)
    talk_form = TalkForm(request.POST or None)
    participant_form = ParticipantForm(request.POST or None)
    forms = [talk_form, participant_form]
    if request.method == 'POST' and all([form.is_valid() for form in forms]):
        talk = talk_form.save(commit=False)
        talk.site = get_current_site(request)
        email = participant.cleaned_data['email']
        try:
            participant = Participant.objects.get(email=email)
        except Participant.DoesNoExist:
             participant = participant_form.save()
        talk.participant = participant
        talk.save()
        return redirect(reverse('propose-complete'))
    return render('cfp/propose.html', {
        'talk_form': talk_form,
        'participant_form': participant_form,
    })


class CompleteView(TemplateView):
    template_name = 'cfp/complete.html'
