from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username:
            return None
        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get(email__iexact=username)
        except UserModel.DoesNotExist:
            UserModel().set_password(password) # https://code.djangoproject.com/ticket/20760
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
