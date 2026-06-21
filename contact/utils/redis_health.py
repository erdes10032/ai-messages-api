import logging

import redis
from django.conf import settings

logger = logging.getLogger('contact')


def check_redis_connection() -> bool:
    """Прямая проверка Redis, не зависит от IGNORE_EXCEPTIONS в cache backend."""
    try:
        client = redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        return client.ping()
    except Exception as exc:
        logger.warning('Redis health check failed: %s', exc)
        return False
