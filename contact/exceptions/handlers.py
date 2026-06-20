import logging

from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler

logger = logging.getLogger('contact')


class RateLimitExceeded(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Слишком много запросов. Попробуйте позже.'
    default_code = 'rate_limit_exceeded'


class EmailDeliveryError(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'Не удалось отправить уведомление. Попробуйте позже.'
    default_code = 'email_delivery_failed'


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_body = {
            'error': exc.default_code if hasattr(exc, 'default_code') else 'error',
            'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
        }
        if isinstance(exc, ValidationError) and isinstance(exc.detail, dict):
            error_body['details'] = exc.detail
            error_body['error'] = 'validation_error'
            error_body['message'] = 'Ошибка валидации данных.'

        response.data = error_body
        return response

    logger.exception('Unhandled exception in %s', context.get('view'))
    return JsonResponse(
        {'error': 'internal_error', 'message': 'Внутренняя ошибка сервера.'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
