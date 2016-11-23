from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^enrole/$', views.enrole, name='enrole-as-volunteer'),
    url(r'^enrole/(?P<slug>[-\w]+)/$', views.enrole, name='enrole-as-volunteer'),
    url(r'^list/$', views.volunteer_list, name='list-volunteers'),
    url(r'^activities/$', views.ActivityList.as_view(), name='list-activities'),
    url(r'^activities/add/$', views.ActivityCreate.as_view(), name='add-activity'),
    url(r'^activities/(?P<slug>[-\w]+)/edit/$', views.ActivityUpdate.as_view(), name='edit-activity'),
]
