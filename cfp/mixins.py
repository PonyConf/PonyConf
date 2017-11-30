from django.contrib.auth.mixins import UserPassesTestMixin

from .utils import is_staff


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_staff(self.request, self.request.user)


class OnSiteAdminMixin:
    exclude = ('site',)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.site = request.site
        super().save_model(request, obj, form, change)
