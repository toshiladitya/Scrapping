from django.urls import path
from core.views import *

urlpatterns = [
    path('', scrape_view, name='scrape_view'),
    path('download-csv/', download_csv, name='download_csv'),
]