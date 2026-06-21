import logging
import time

from django.utils.deprecation import MiddlewareMixin

from contact.repositories.log_repository import RequestLogRepository
from contact.utils.sanitizers import get_client_ip

logger = logging.getLogger('contact.requests')


class RequestLoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self._log_repo = RequestLogRepository()

    def process_request(self, request):
        request._start_time = time.monotonic()
        return None

    def process_response(self, request, response):
        if not request.path.startswith('/api/'):
            return response

        duration_ms = int((time.monotonic() - getattr(request, '_start_time', time.monotonic())) * 1000)
        client_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        logger.info(
            '%s %s %s %dms ip=%s',
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            client_ip,
        )

        try:
            self._log_repo.create(
                method=request.method,
                path=request.path[:255],
                status_code=response.status_code,
                client_ip=client_ip,
                duration_ms=duration_ms,
                user_agent=user_agent,
            )
        except Exception:
            logger.exception('Failed to persist request log')

        return response
