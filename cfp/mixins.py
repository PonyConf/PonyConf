from django.contrib.auth.mixins import UserPassesTestMixin

from .utils import is_staff


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_staff(self.request, self.request.user)


class OnSiteMixin:
    def get_queryset(self):
        return super().get_queryset().filter(site=self.kwargs['conference'].site)
