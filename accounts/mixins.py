from django.contrib.auth.mixins import UserPassesTestMixin

from .utils import is_orga, is_staff


class OrgaRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_orga(self.request, self.request.user)


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_staff(self.request, self.request.user)
