from django.conf.urls import url

from proposals import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^talk/$', views.talk_list, name='list-talks'),
    url(r'^talk/add/$', views.talk_edit, name='add-talk'),
    url(r'^talk/edit/(?P<talk>[-\w]+)$', views.talk_edit, name='edit-talk'),
    url(r'^talk/details/(?P<slug>[-\w]+)$', views.TalkDetail.as_view(), name='show-talk'),
    url(r'^talk/by-topic/(?P<topic>[-\w]+)$', views.talk_list_by_topic, name='list-talks-by-topic'),
    url(r'^talk/by-speaker/(?P<speaker>[\w.@+-]+)$', views.talk_list_by_speaker, name='list-talks-by-speaker'),
    url(r'^topic/$', views.TopicList.as_view(), name='list-topics'),
    url(r'^speakers/$', views.SpeakerList.as_view(), name='list-speakers'),
    url(r'^user/(?P<username>[\w.@+-]+)$', views.user_details, name='show-user'),
]
