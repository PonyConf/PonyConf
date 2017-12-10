from django.urls import include, path
from django.contrib import admin
from django.conf import settings

from . import views


urlpatterns = [
    path('markdown/', views.markdown_preview, name='markdown-preview'),
    path('admin/django/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('cfp.urls')),
]

if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
