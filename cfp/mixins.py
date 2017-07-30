from django.contrib.auth.mixins import UserPassesTestMixin

from .utils import is_staff


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_staff(self.request, self.request.user)
