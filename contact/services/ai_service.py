import json
import logging
import re
from typing import Any

import httpx
from django.conf import settings
from django.core.cache import cache

from contact.services.types import AIAnalysisResult, AIServiceError
from contact.utils.sanitizers import hash_for_cache

logger = logging.getLogger('contact')

OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'

SYSTEM_PROMPT = """Ты — ассистент backend-сервиса обратной связи разработчика.
Проанализируй обращение пользователя и верни ТОЛЬКО валидный JSON без markdown:
{
  "sentiment": "positive|neutral|negative",
  "category": "bug|feature|collaboration|question|spam|general",
  "reply": "вежливый персональный ответ на русском, 2-4 предложения"
}
Правила:
- sentiment: эмоциональный тон комментария
- category: тип запроса (spam — если реклама, бессмыслица, оскорбления)
- reply: черновик ответа от имени разработчика, без обещаний которые нельзя выполнить"""


class AIService:
    def analyze(self, name: str, comment: str) -> AIAnalysisResult:
        cache_key = f'ai:{hash_for_cache(comment)}'
        cached = cache.get(cache_key)
        if cached:
            return AIAnalysisResult(**cached)

        try:
            result = self._call_openrouter(name, comment, settings.OPENROUTER_MODEL)
            cache.set(cache_key, result.__dict__, timeout=3600)
            return result
        except AIServiceError as primary_error:
            logger.warning('Primary AI model failed: %s', primary_error)
            try:
                result = self._call_openrouter(name, comment, settings.OPENROUTER_FALLBACK_MODEL)
                cache.set(cache_key, result.__dict__, timeout=3600)
                return result
            except AIServiceError as fallback_error:
                logger.error('Fallback AI model failed: %s', fallback_error)
                return self._rule_based_fallback(name, comment)

    def _call_openrouter(self, name: str, comment: str, model: str) -> AIAnalysisResult:
        if not settings.OPENROUTER_API_KEY:
            raise AIServiceError('OPENROUTER_API_KEY is not configured')

        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': f'Имя: {name}\nКомментарий: {comment}'},
            ],
            'temperature': 0.3,
            'max_tokens': 400,
        }
        headers = {
            'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://presentation-api.onrender.com',
            'X-Title': 'Presentation API',
        }

        try:
            with httpx.Client(timeout=settings.OPENROUTER_TIMEOUT_SECONDS) as client:
                response = client.post(OPENROUTER_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:300]
            logger.warning('OpenRouter HTTP %s for model %s: %s', exc.response.status_code, model, body)
            raise AIServiceError(f'HTTP {exc.response.status_code}: {body}') from exc
        except httpx.HTTPError as exc:
            logger.warning('OpenRouter network error for model %s: %s', model, exc)
            raise AIServiceError(str(exc)) from exc
        except Exception as exc:
            raise AIServiceError(str(exc)) from exc

        content = data['choices'][0]['message']['content']
        parsed = self._parse_ai_response(content)
        return AIAnalysisResult(
            sentiment=parsed['sentiment'],
            category=parsed['category'],
            reply=parsed['reply'],
            ai_used=True,
        )

    def _parse_ai_response(self, content: str) -> dict[str, str]:
        content = content.strip()
        if content.startswith('```'):
            content = re.sub(r'^```(?:json)?\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

        try:
            data: dict[str, Any] = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIServiceError(f'Invalid JSON from AI: {content[:200]}') from exc

        sentiment = data.get('sentiment', 'neutral')
        category = data.get('category', 'general')
        reply = data.get('reply', '')

        valid_sentiments = {'positive', 'neutral', 'negative'}
        valid_categories = {'bug', 'feature', 'collaboration', 'question', 'spam', 'general'}

        if sentiment not in valid_sentiments:
            sentiment = 'neutral'
        if category not in valid_categories:
            category = 'general'
        if not reply:
            raise AIServiceError('Empty reply from AI')

        return {'sentiment': sentiment, 'category': category, 'reply': reply}

    def _rule_based_fallback(self, name: str, comment: str) -> AIAnalysisResult:
        lower = comment.lower()

        negative_words = ('плохо', 'ужас', 'не работает', 'ошибка', 'баг', 'разочарован')
        positive_words = ('спасибо', 'отлично', 'класс', 'супер', 'круто', 'нравится')

        if any(w in lower for w in negative_words):
            sentiment = 'negative'
        elif any(w in lower for w in positive_words):
            sentiment = 'positive'
        else:
            sentiment = 'neutral'

        if any(w in lower for w in ('баг', 'ошибка', 'не работает', 'сломал')):
            category = 'bug'
        elif any(w in lower for w in ('предлож', 'идея', 'добав', 'функци')):
            category = 'feature'
        elif any(w in lower for w in ('сотруднич', 'проект', 'работ', 'ваканс', 'нанять')):
            category = 'collaboration'
        elif '?' in comment or any(w in lower for w in ('как', 'почему', 'сколько', 'вопрос')):
            category = 'question'
        elif any(w in lower for w in ('купить', 'скидк', 'реклам', 'казино', 'крипт')):
            category = 'spam'
        else:
            category = 'general'

        reply = (
            f'Здравствуйте, {name}! Спасибо за ваше обращение. '
            f'Я получил ваше сообщение и отвечу в ближайшее время.'
        )

        return AIAnalysisResult(
            sentiment=sentiment,
            category=category,
            reply=reply,
            ai_used=False,
        )
