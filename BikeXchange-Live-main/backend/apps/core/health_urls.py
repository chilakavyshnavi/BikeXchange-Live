"""
URL configuration for health check endpoints.
"""

from django.urls import path
from . import health

urlpatterns = [
    path('', health.health_check, name='health-check'),
    path('ready/', health.readiness_check, name='readiness-check'),
]
