# core/urls.py

from django.urls import path
from django.urls import path, include

urlpatterns = [
    path('api/auth/', include('users.urls')),
    path('solicitudes/', include('solicitudes.urls')),
]