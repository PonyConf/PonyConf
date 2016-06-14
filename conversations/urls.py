from django.conf.urls import url

from conversations import views, emails


urlpatterns = [
    url(r'^recv/$', emails.email_recv),
    url(r'^$', views.messaging, name='messaging'),
]
