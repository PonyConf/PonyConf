from django.conf.urls import url

from conversations import views

urlpatterns = [
    url(r'^(?P<conversation>[0-9]+)$', views.conversation_details, name='show-conversation'),
]
