from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^login/$', auth_views.login, {'extra_context': {'buttons': [views.RESET_PASSWORD_BUTTON]}}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
    url(r'^participant/$', views.participation_list, name='list-participants'),
    url(r'^participant/(?P<username>[\w.@+-]+)$', views.participant_details, name='show-participant'),
    url(r'^participant/(?P<username>[\w.@+-]+)/edit/$', views.participant_edit, name='edit-participant'),
    url(r'^avatar/', include('avatar.urls')),
    url(r'', include('django.contrib.auth.urls')),
    url(r'', include('registration.backends.default.urls')),
]
