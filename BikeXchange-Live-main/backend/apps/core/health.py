"""
Health check and system observability views.
"""

import time
import platform

from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

# Server start time for uptime calculation
_start_time = time.time()


@extend_schema(tags=['Health'])
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint.
    
    Returns system status including:
    - Service status
    - Database connectivity
    - Uptime
    - System info
    """
    # Check database
    db_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:
        db_ok = False

    uptime_seconds = int(time.time() - _start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return Response({
        'status': 'healthy' if db_ok else 'degraded',
        'timestamp': timezone.now().isoformat(),
        'uptime': f'{hours}h {minutes}m {seconds}s',
        'uptime_seconds': uptime_seconds,
        'database': 'connected' if db_ok else 'disconnected',
        'python_version': platform.python_version(),
        'system': platform.system(),
    })


@extend_schema(tags=['Health'])
@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness probe for container orchestration.
    
    Returns 200 if the service is ready to accept traffic,
    503 if critical dependencies are unavailable.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return Response({'ready': True})
    except Exception:
        return Response(
            {'ready': False, 'reason': 'Database unavailable'},
            status=503,
        )
