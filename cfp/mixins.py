from django.contrib.auth.mixins import UserPassesTestMixin

from .utils import is_staff


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_staff(self.request, self.request.user)


class OnSiteMixin:
    def get_queryset(self):
        return super().get_queryset().filter(site=self.request.conference.site)


class OnSiteFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'conference': self.request.conference,
        })
        return kwargs


class OnSiteAdminMixin:
    exclude = ('site',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(site=request.conference.site)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.site = request.conference.site
        super().save_model(request, obj, form, change)
