from django.conf.urls import url

from conversations import emails, views

urlpatterns = [
    url(r'^recv/$', emails.email_recv),
    url(r'^inbox/$', views.conversation, name='inbox'),
    url(r'^$', views.correspondents, name='correspondents'),
    url(r'^with/(?P<username>[\w.@+-]+)/$', views.conversation, name='conversation'),
    url(r'^about/(?P<talk>[\w.@+-]+)/$', views.talk_conversation, name='talk-conversation'),
    url(r'^subscribe/(?P<username>[\w.@+-]+)/$', views.subscribe, name='subscribe-conversation'),
    url(r'^unsubscribe/(?P<username>[\w.@+-]+)/$', views.unsubscribe, name='unsubscribe-conversation'),
]
