from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from django.conf.urls.static import static

from photo import urls as photo_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(photo_urls)),
    path('celery-progress/', include('celery_progress.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
