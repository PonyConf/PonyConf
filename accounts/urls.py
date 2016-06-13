from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

from .views import profile

urlpatterns = [
    url(r'^profile$', profile, name='profile'),
    url(r'^logout/$', auth_views.logout, {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
    url(r'', include('django.contrib.auth.urls')),
]
