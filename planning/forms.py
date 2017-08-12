from django import forms

from .models import Room


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'label', 'capacity']

    def __init__(self, *args, **kwargs):
        self.site = kwargs.pop('site')
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name']
        if (not self.instance or self.instance.name != name) \
                and Room.objects.filter(site=self.site, name=name).exists():
            raise self.instance.unique_error_message(self._meta.model, ['name'])
        return name
