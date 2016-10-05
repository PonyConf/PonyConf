from django.contrib.sites.shortcuts import get_current_site


class OnSiteFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'site': get_current_site(self.request)})
        return kwargs

    def form_valid(self, form):
        form.instance.site = get_current_site(self.request)
        return super().form_valid(form)
