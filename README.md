# AI Messages API

Backend-сервис для лендинг-презентации разработчика: REST API обратной связи с AI-анализом, email-уведомлениями и защитой от спама.

## Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Backend | Python 3.12, Django 5+, Django REST Framework |
| БД | PostgreSQL |
| Кеш / Rate limit | Redis (django-redis) |
| AI | OpenRouter API |
| Email | SMTP (Yandex) |
| Документация | drf-spectacular (OpenAPI / Swagger) |
| Деплой | Render + Gunicorn + WhiteNoise |


API доступен на `https://ai-messages-api.onrender.com/api/`

**Лендинг:** `https://ai-messages-api.onrender.com/` (Bootstrap + форма обратной связи)

Swagger UI: `https://ai-messages-api.onrender.com/api/docs/`

### 4. Тесты

```bash
python manage.py test contact
```

## Переменные окружения

| Переменная | Описание |
|-----------|----------|
| `SECRET_KEY` | Секретный ключ Django |
| `DEBUG` | Режим отладки (`True`/`False`) |
| `ALLOWED_HOSTS` | Разрешённые хосты через запятую |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL (локально) |
| `DATABASE_URL` | PostgreSQL URL (Render) |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_USE_SSL` | Redis (локально) |
| `REDIS_URL` | Redis URL (Render) |
| `RATE_LIMIT_REQUESTS` | Макс. запросов за окно (по умолчанию 5) |
| `RATE_LIMIT_WINDOW_SECONDS` | Окно rate limit в секундах (по умолчанию 900) |
| `OPENROUTER_API_KEY` | API-ключ OpenRouter |
| `OPENROUTER_MODEL` | Основная AI-модель |
| `OPENROUTER_FALLBACK_MODEL` | Резервная AI-модель |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_SSL` | SMTP-настройки |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Учётные данные SMTP |
| `DEFAULT_FROM_EMAIL`, `EMAIL_ADMIN` | Отправитель и получатель заявок |
| `CORS_ALLOWED_ORIGINS` | Разрешённые origins для CORS |

## Архитектура

```
Controllers (views.py)
    ↓
Services (contact_service, ai_service, email_service)
    ↓
Repositories (contact_repository, log_repository)
    ↓
Models (PostgreSQL)
```

**Паттерны:**
- Слоистая архитектура (Controller → Service → Repository)
- Graceful degradation (AI fallback при недоступности API)
- Honeypot-поле `website` для защиты от ботов
- Rate limiting через Redis
- Санитизация входных данных (bleach)

```
presentation-api/
├── config/              # Настройки Django
├── contact/
│   ├── middleware/      # Логирование, rate limit
│   ├── services/        # Бизнес-логика + AI + Email
│   ├── repositories/    # Работа с БД
│   ├── serializers/     # Валидация API
│   ├── exceptions/      # Обработка ошибок
│   ├── templates/       # Email-шаблоны
│   └── tests/           # Тесты
├── logs/                # Файлы логов
├── requirements.txt
├── render.yaml          # Blueprint для Render
└── build.sh             # Скрипт сборки
```

## API

### POST /api/contact

Отправка формы обратной связи.

**Запрос:**
```bash
curl -X POST https://ai-messages-api.onrender.com/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Иван Петров",
    "phone": "+7 (999) 123-45-67",
    "email": "ivan@example.com",
    "comment": "Хотел бы обсудить сотрудничество по проекту."
  }'
```

**Ответ (201):**
```json
{
  "id": "uuid",
  "message": "Обращение получено и будет обработано.",
  "ai_sentiment": "positive",
  "ai_category": "collaboration",
  "ai_reply": "Спасибо за интерес! Свяжусь с вами в ближайшее время.",
  "ai_used": true
}
```

**Ошибки:**
| Код | Описание |
|-----|----------|
| 400 | Ошибка валидации |
| 429 | Превышен лимит запросов |
| 502 | Ошибка отправки email |
| 500 | Внутренняя ошибка |

### GET /api/health

Проверка состояния сервиса (БД + Redis).

### GET /api/metrics

Статистика обращений: общее количество, по категориям, тональности, AI/fallback, спам.

## AI-интеграция

Один запрос к OpenRouter выполняет три задачи:

1. **Анализ тональности** — positive / neutral / negative
2. **Классификация запроса** — bug / feature / collaboration / question / spam / general
3. **Генерация ответа** — черновик персонального ответа на русском

**Fallback-цепочка:**
1. Основная модель (`OPENROUTER_MODEL`)
2. Резервная модель (`OPENROUTER_FALLBACK_MODEL`)
3. Rule-based классификатор (ключевые слова) — сервис продолжает работать

**Кеширование:** результаты AI кешируются в Redis на 1 час по хешу комментария.

## Email

| Окружение | Способ |
|-----------|--------|
| **Локально** | Yandex SMTP (`EMAIL_HOST_*`) |
| **Render** | [Resend API](https://resend.com) — SMTP на Free plan заблокирован |

Если задан `RESEND_API_KEY` — письма идут через HTTPS API Resend.  
Иначе — стандартный Django SMTP.

## Безопасность

- Валидация и санитизация всех полей (bleach, regex)
- Honeypot-поле `website` (скрытое от пользователя)
- Rate limiting по IP через Redis
- CORS whitelist
- Маскирование PII в логах
- `SECRET_KEY` и API-ключи только в `.env`
- Security headers в production (HSTS, XSS, nosniff)
- HTTPS redirect на Render

## Хранение данных

| Данные | Где |
|--------|-----|
| Обращения | PostgreSQL (`ContactRequest`) |
| Логи запросов | PostgreSQL (`RequestLog`) + файл `logs/requests.log` |
| Rate limit | Redis |
| AI-кеш | Redis |
| App-логи | `logs/app.log` (ротация 5 МБ) |

