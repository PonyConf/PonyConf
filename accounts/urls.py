from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

from .views import profile
from ponyconf.settings import LOGOUT_REDIRECT_URL

urlpatterns = [
    url(r'^profile$', profile, name='profile'),
    url(r'^logout/$', auth_views.logout, {'next_page': LOGOUT_REDIRECT_URL}, name='logout'),
    url(r'', include('django.contrib.auth.urls')),
]
