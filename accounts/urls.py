from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^register/$', views.Registration.as_view(), name='register'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^login/$', auth_views.login, {'extra_context': {'buttons': [views.RESET_PASSWORD_BUTTON]}}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
    url(r'^admin/participants/$', views.ParticipantList.as_view(), name='list-participant'),
    url(r'^admin/participant/(?P<username>[\w.@+-]+)$', views.edit, name='edit-participant'),
    url(r'', include('django.contrib.auth.urls')),
]
