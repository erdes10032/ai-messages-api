import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from contact.exceptions.handlers import RateLimitExceeded
from contact.utils.sanitizers import get_client_ip

logger = logging.getLogger('contact')

RATE_LIMITED_PATHS = ('/api/contact',)


class RateLimitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.method != 'POST':
            return None

        if not any(request.path.startswith(p) for p in RATE_LIMITED_PATHS):
            return None

        client_ip = get_client_ip(request)
        if not client_ip:
            return None

        cache_key = f'ratelimit:{client_ip}'
        request_count = cache.get(cache_key, 0)

        if request_count >= settings.RATE_LIMIT_REQUESTS:
            logger.warning('Rate limit exceeded for IP %s', client_ip)
            exc = RateLimitExceeded()
            return JsonResponse(
                {'error': exc.default_code, 'message': str(exc.detail)},
                status=exc.status_code,
            )

        if request_count == 0:
            cache.set(cache_key, 1, timeout=settings.RATE_LIMIT_WINDOW_SECONDS)
        else:
            cache.incr(cache_key)

        return None
