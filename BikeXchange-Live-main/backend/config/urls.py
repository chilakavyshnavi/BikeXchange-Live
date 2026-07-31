"""
Root URL configuration for Vutto Bike Auction Platform.

Routes:
    /api/auth/       — Authentication & user management
    /api/auctions/   — Auction browsing & management
    /api/admin-api/  — Administrative dashboard endpoints
    /api/health/     — System health checks
    /api/docs/       — Interactive API documentation (Swagger)
    /admin/          — Django built-in admin panel
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # API routes
    path('api/auth/', include('apps.accounts.urls')),
    path('api/auctions/', include('apps.auctions.urls')),
    path('api/health/', include('apps.core.health_urls')),

    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin site customization
admin.site.site_header = 'Vutto Bike Auction Admin'
admin.site.site_title = 'Vutto Auctions'
admin.site.index_title = 'Platform Management'
