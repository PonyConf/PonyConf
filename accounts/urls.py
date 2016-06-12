from django.conf.urls import include, url

from .views import profile

urlpatterns = [
    url(r'^profile$', profile, name='profile'),
    url(r'', include('django.contrib.auth.urls')),
]
