from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^profile$', views.profile, name='profile'),
    url(r'^logout/$', auth_views.logout, {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
    url(r'^admin/participants/$', views.participants, name='participants'),
    url(r'', include('django.contrib.auth.urls')),
]
