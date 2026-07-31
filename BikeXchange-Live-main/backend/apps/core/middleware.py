"""
Custom middleware for request logging and error handling.

Provides:
- RequestLoggingMiddleware: Logs every HTTP request with method, path, status, duration
- custom_exception_handler: DRF exception handler with structured error responses
"""

import time
import uuid
import logging

from django.utils.deprecation import MiddlewareMixin
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('apps.core.middleware')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Logs HTTP requests with timing and request ID correlation.
    
    Adds an X-Request-ID header to every response for tracing.
    Logs: method, path, status code, response time, user.
    """

    def process_request(self, request):
        request.start_time = time.time()
        request.request_id = str(uuid.uuid4())[:8]

    def process_response(self, request, response):
        # Calculate request duration
        duration = time.time() - getattr(request, 'start_time', time.time())
        duration_ms = round(duration * 1000, 2)

        # Add request ID to response headers
        request_id = getattr(request, 'request_id', 'unknown')
        response['X-Request-ID'] = request_id

        # Determine user
        user = getattr(request, 'user', None)
        user_str = user.email if user and hasattr(user, 'email') and user.is_authenticated else 'anonymous'

        # Log the request
        log_data = (
            f'[{request_id}] {request.method} {request.path} '
            f'→ {response.status_code} ({duration_ms}ms) '
            f'user={user_str}'
        )

        if response.status_code >= 500:
            logger.error(log_data)
        elif response.status_code >= 400:
            logger.warning(log_data)
        else:
            logger.info(log_data)

        return response


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler that returns structured error responses.
    
    Response format:
    {
        "error": true,
        "message": "Human-readable error message",
        "details": { ... }  // Optional validation errors
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'error': True,
            'message': _get_error_message(response, exc),
        }

        # Include validation details if available
        if isinstance(response.data, dict):
            # Filter out the 'detail' key since we already use it as message
            details = {
                k: v for k, v in response.data.items()
                if k != 'detail'
            }
            if details:
                error_data['details'] = details

        response.data = error_data

    return response


def _get_error_message(response, exc):
    """Extract a human-readable error message."""
    if hasattr(response, 'data'):
        if isinstance(response.data, dict):
            detail = response.data.get('detail')
            if detail:
                return str(detail)
        elif isinstance(response.data, list) and response.data:
            return str(response.data[0])

    status_messages = {
        400: 'Bad request.',
        401: 'Authentication required.',
        403: 'Permission denied.',
        404: 'Resource not found.',
        405: 'Method not allowed.',
        429: 'Too many requests. Please slow down.',
        500: 'Internal server error.',
    }

    return status_messages.get(response.status_code, str(exc))
