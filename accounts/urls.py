from django.conf import settings
from django.urls import include, path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('accounts/login/', views.EmailLoginView.as_view(), {'extra_context': {'buttons': [views.RESET_PASSWORD_BUTTON]}}, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
    path('', include('django.contrib.auth.urls')),
]
