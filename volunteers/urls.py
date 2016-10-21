from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^enrole/$', views.participate, name='participate-as-volunteer'),
    url(r'^activities/$', views.ActivityList.as_view(), name='list-activities'),
    url(r'^activities/add/$', views.ActivityCreate.as_view(), name='add-activity'),
    url(r'^activities/(?P<slug>[-\w]+)/edit/$', views.ActivityUpdate.as_view(), name='edit-activity'),
    url(r'^activities/(?P<slug>[-\w]+)/enrole/$', views.participate, name='enrole-in-activity'),
]
