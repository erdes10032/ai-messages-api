from unittest.mock import MagicMock, patch

import httpx
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from contact.models import ContactRequest
from contact.services.ai_service import AIService
from contact.services.types import AIAnalysisResult


class ContactAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_payload = {
            'name': 'Иван Петров',
            'phone': '+7 (999) 123-45-67',
            'email': 'ivan@example.com',
            'comment': 'Хотел бы обсудить сотрудничество по проекту.',
        }
        cache.clear()

    @patch('contact.services.contact_service.EmailService.send_contact_notifications')
    @patch('contact.services.contact_service.AIService.analyze')
    def test_contact_success(self, mock_analyze, mock_email):
        mock_analyze.return_value = AIAnalysisResult(
            sentiment='positive',
            category='collaboration',
            reply='Спасибо за интерес! Свяжусь с вами.',
            ai_used=True,
        )

        response = self.client.post('/api/contact', self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['ai_category'], 'collaboration')
        self.assertTrue(response.data['ai_used'])
        mock_email.assert_called_once()
        self.assertEqual(ContactRequest.objects.count(), 1)

    def test_contact_validation_error_short_name(self):
        payload = {**self.valid_payload, 'name': 'А'}
        response = self.client.post('/api/contact', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'validation_error')

    def test_contact_validation_invalid_phone(self):
        payload = {**self.valid_payload, 'phone': 'abc'}
        response = self.client.post('/api/contact', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_contact_validation_invalid_email(self):
        payload = {**self.valid_payload, 'email': 'not-an-email'}
        response = self.client.post('/api/contact', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_honeypot_rejects_spam(self):
        payload = {**self.valid_payload, 'website': 'http://spam.com'}
        response = self.client.post('/api/contact', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('contact.services.contact_service.EmailService.send_contact_notifications')
    @patch('contact.services.contact_service.AIService.analyze')
    def test_spam_skips_email(self, mock_analyze, mock_email):
        mock_analyze.return_value = AIAnalysisResult(
            sentiment='neutral',
            category='spam',
            reply='',
            ai_used=True,
        )

        response = self.client.post('/api/contact', self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_email.assert_not_called()

    @patch('contact.services.contact_service.EmailService.send_contact_notifications')
    @patch('contact.services.contact_service.AIService.analyze')
    def test_contact_email_delivery_error_returns_502(self, mock_analyze, mock_email):
        mock_analyze.return_value = AIAnalysisResult(
            sentiment='neutral',
            category='general',
            reply='Спасибо за обращение.',
            ai_used=True,
        )
        mock_email.side_effect = Exception('SMTP connection failed')

        response = self.client.post('/api/contact', self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(response.data['error'], 'email_delivery_failed')
        self.assertEqual(ContactRequest.objects.count(), 1)
        mock_email.assert_called_once()


class AIServiceTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.service = AIService()

    @patch('contact.services.ai_service.httpx.Client')
    def test_ai_success(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '{"sentiment":"positive","category":"question","reply":"Ответ"}'}}],
        }
        mock_response.raise_for_status = MagicMock()
        mock_client_cls.return_value.__enter__.return_value.post.return_value = mock_response

        result = self.service.analyze('Иван', 'Как связаться с вами?')
        self.assertEqual(result.sentiment, 'positive')
        self.assertEqual(result.category, 'question')
        self.assertTrue(result.ai_used)

    @patch('contact.services.ai_service.httpx.Client')
    def test_ai_fallback_on_failure(self, mock_client_cls):
        mock_client_cls.return_value.__enter__.return_value.post.side_effect = httpx.ConnectError(
            'API down',
        )

        result = self.service.analyze('Иван', 'У меня ошибка в проекте, не работает форма')
        self.assertFalse(result.ai_used)
        self.assertEqual(result.category, 'bug')
        self.assertEqual(result.sentiment, 'negative')


@override_settings(
    RATE_LIMIT_REQUESTS=2,
    RATE_LIMIT_WINDOW_SECONDS=60,
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'rate-limit-test',
        }
    },
)
class RateLimitTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()

    @patch('contact.services.contact_service.EmailService.send_contact_notifications')
    @patch('contact.services.contact_service.AIService.analyze')
    def test_rate_limit_blocks_excess_requests(self, mock_analyze, mock_email):
        mock_analyze.return_value = AIAnalysisResult(
            sentiment='neutral', category='general', reply='OK', ai_used=False,
        )
        payload = {
            'name': 'Тест Тестов',
            'phone': '+79991234567',
            'email': 'test@example.com',
            'comment': 'Тестовое сообщение для проверки лимита.',
        }

        for _ in range(2):
            response = self.client.post('/api/contact', payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post('/api/contact', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class HealthMetricsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_endpoint(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('checks', response.data)

    def test_metrics_endpoint(self):
        ContactRequest.objects.create(
            name='Test', phone='+79990000000', email='t@t.com',
            comment='Test comment here', ai_category='general', ai_sentiment='neutral',
        )
        response = self.client.get('/api/metrics')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_requests'], 1)
