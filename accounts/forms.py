from django.forms.models import modelform_factory
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User


__all__ = ['ProfileForm']


ProfileForm = modelform_factory(User,
        fields=['first_name', 'last_name', 'email', 'biography'])

class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('biography',)
