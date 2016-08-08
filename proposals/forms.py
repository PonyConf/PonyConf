from django.forms import CheckboxSelectMultiple, ModelForm
from django.forms.models import modelform_factory
from django.core.exceptions import ValidationError

from django_select2.forms import Select2TagWidget

from proposals.models import Talk, Topic


class TalkForm(ModelForm):
    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super(TalkForm, self).__init__(*args, **kwargs)
        self.fields['topics'].queryset = Topic.objects.filter(site=site)

    class Meta:
        model = Talk
        fields = ['title', 'abstract', 'description', 'topics', 'notes', 'event', 'speakers']
        widgets = {'topics': CheckboxSelectMultiple(), 'speakers': Select2TagWidget()}


class TopicCreateForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.site_id = kwargs.pop('site_id')
        super(TopicCreateForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Topic
        fields = ['name', 'description', 'reviewers']
        widgets = {'reviewers': Select2TagWidget()}

    def clean_name(self):
        name = self.cleaned_data['name']
        if name != self.instance.name and Topic.objects.filter(site__id=self.site_id, name=name).exists():
            raise self.instance.unique_error_message(self._meta.model, ['name'])
        return name


TopicUpdateForm = modelform_factory(Topic, fields=['reviewers'],
                                    widgets={'reviewers': Select2TagWidget()})
