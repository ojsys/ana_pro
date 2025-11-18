"""
Custom middleware for enhanced error logging and tracking.
"""
import logging
import traceback
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('dashboard')


class ErrorLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log detailed error information including request context.
    """

    def process_exception(self, request, exception):
        """
        Log detailed information when an exception occurs.
        """
        # Get user information
        user_info = 'Anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info = f"{request.user.username} (ID: {request.user.id})"

        # Get request details
        request_path = request.path
        request_method = request.method
        request_get = dict(request.GET)
        request_post = dict(request.POST)

        # Sanitize sensitive data
        sensitive_keys = ['password', 'token', 'secret', 'api_key']
        for key in sensitive_keys:
            if key in request_post:
                request_post[key] = '***REDACTED***'

        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Log comprehensive error information
        error_message = f"""
{'='*80}
EXCEPTION OCCURRED
{'='*80}
Error Type: {type(exception).__name__}
Error Message: {str(exception)}

Request Information:
-------------------
User: {user_info}
IP Address: {ip}
Method: {request_method}
Path: {request_path}
GET Parameters: {request_get}
POST Parameters: {request_post}

User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}
Referer: {request.META.get('HTTP_REFERER', 'None')}

Stack Trace:
------------
{traceback.format_exc()}
{'='*80}
"""

        logger.error(error_message)

        # Don't interfere with normal exception handling
        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all requests (useful for debugging).
    Enable by setting LOG_ALL_REQUESTS=True in environment.
    """

    def process_request(self, request):
        """Log incoming requests."""
        from django.conf import settings
        from decouple import config

        if config('LOG_ALL_REQUESTS', default=False, cast=bool):
            user_info = 'Anonymous'
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_info = request.user.username

            logger.info(
                f"Request: {request.method} {request.path} | "
                f"User: {user_info} | "
                f"IP: {request.META.get('REMOTE_ADDR', 'Unknown')}"
            )

        return None

    def process_response(self, request, response):
        """Log response status."""
        from decouple import config

        if config('LOG_ALL_REQUESTS', default=False, cast=bool):
            logger.info(
                f"Response: {request.method} {request.path} | "
                f"Status: {response.status_code}"
            )

        return response
