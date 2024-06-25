from django.urls import path
from core.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', scrape_view, name='scrape_view'),
    path('download-csv/', download_csv, name='download_csv'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
