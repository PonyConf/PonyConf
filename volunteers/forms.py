from django import forms

from .models import Activity


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields=['name', 'description', 'participants']


class VolunteerFilterForm(forms.Form):
    activity = forms.MultipleChoiceField(
               required=False,
               widget=forms.CheckboxSelectMultiple,
               choices=[],
   )

    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site')
        super().__init__(*args, **kwargs)
        activities = Activity.objects.filter(site=site)
        self.fields['activity'].choices = activities.values_list('slug', 'name')
