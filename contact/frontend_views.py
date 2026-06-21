import logging

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from contact.exceptions.handlers import EmailDeliveryError
from contact.serializers.contact import ContactSerializer
from contact.services.contact_service import ContactService
from contact.utils.sanitizers import get_client_ip

logger = logging.getLogger('contact')


def _check_rate_limit(request) -> bool:
    from django.conf import settings
    from django.core.cache import cache

    client_ip = get_client_ip(request)
    if not client_ip:
        return False

    cache_key = f'ratelimit:{client_ip}'
    request_count = cache.get(cache_key, 0)
    if request_count >= settings.RATE_LIMIT_REQUESTS:
        return True

    if request_count == 0:
        cache.set(cache_key, 1, timeout=settings.RATE_LIMIT_WINDOW_SECONDS)
    else:
        cache.incr(cache_key)
    return False


class LandingView(View):
    template_name = 'landing/index.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        if _check_rate_limit(request):
            messages.error(request, 'Слишком много запросов. Попробуйте позже.')
            return redirect('landing')

        serializer = ContactSerializer(data=request.POST)
        if not serializer.is_valid():
            return render(request, self.template_name, {
                'form_data': request.POST,
                'errors': serializer.errors,
            })

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
            messages.error(request, 'Не удалось отправить письмо. Попробуйте позже.')
            return render(request, self.template_name, {'form_data': request.POST})

        messages.success(request, 'Обращение получено и будет обработано.')
        return render(request, self.template_name, {
            'success': {
                'ai_sentiment': contact.ai_sentiment,
                'ai_category': contact.ai_category,
                'ai_reply': contact.ai_reply,
                'ai_used': contact.ai_used,
            },
        })
