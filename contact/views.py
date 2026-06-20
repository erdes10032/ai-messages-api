import logging

from django.db import connection
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from contact.exceptions.handlers import EmailDeliveryError
from contact.repositories.contact_repository import ContactRepository
from contact.serializers.contact import ContactResponseSerializer, ContactSerializer
from contact.services.contact_service import ContactService
from contact.utils.redis_health import check_redis_connection
from contact.utils.sanitizers import get_client_ip

logger = logging.getLogger('contact')


class ContactView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=ContactSerializer,
        responses={
            201: ContactResponseSerializer,
            400: OpenApiResponse(description='Ошибка валидации'),
            429: OpenApiResponse(description='Превышен лимит запросов'),
            502: OpenApiResponse(description='Ошибка отправки email'),
        },
        summary='Отправить обращение',
        description='Принимает форму обратной связи, анализирует через AI и отправляет email.',
    )
    def post(self, request: Request) -> Response:
        serializer = ContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        service = ContactService()

        try:
            contact = service.process_contact(
                name=data['name'],
                phone=data['phone'],
                email=data['email'],
                comment=data['comment'],
                client_ip=get_client_ip(request),
            )
        except EmailDeliveryError:
            raise

        is_spam = contact.ai_category == 'spam'
        message = (
            'Обращение получено и будет обработано.'
            if not is_spam
            else 'Сообщение получено.'
        )

        response_data = {
            'id': contact.id,
            'message': message,
            'ai_sentiment': contact.ai_sentiment,
            'ai_category': contact.ai_category,
            'ai_reply': contact.ai_reply if not is_spam else '',
            'ai_used': contact.ai_used,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class HealthView(APIView):
    @extend_schema(
        responses={200: OpenApiResponse(description='Сервис работает')},
        summary='Проверка состояния сервиса',
    )
    def get(self, request: Request) -> Response:
        checks = {
            'database': self._check_database(),
            'redis': self._check_redis(),
        }
        all_healthy = all(checks.values())
        return Response(
            {
                'status': 'ok' if all_healthy else 'degraded',
                'checks': checks,
            },
            status=status.HTTP_200_OK,
        )

    def _check_database(self) -> bool:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            return True
        except Exception:
            return False

    def _check_redis(self) -> bool:
        return check_redis_connection()


class MetricsView(APIView):
    @extend_schema(
        responses={200: OpenApiResponse(description='Статистика обращений')},
        summary='Статистика обращений',
    )
    def get(self, request: Request) -> Response:
        repo = ContactRepository()
        return Response(repo.get_metrics())
