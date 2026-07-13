# AI Messages API

Backend-сервис для лендинг-презентации разработчика: REST API обратной связи с AI-анализом, email-уведомлениями и защитой от спама.

**Production:** https://ai-messages-api.onrender.com/  
**Swagger UI:** https://ai-messages-api.onrender.com/api/docs/

---

## 1. Как запустить проект

### Требования

- [Docker](https://docs.docker.com/get-docker/) и Docker Compose

### Настройка переменных окружения

Все настройки хранятся в .env.example

**Группа 1 — заполните перед запуском:**

| Переменная | Описание |
|------------|----------|
| `SECRET_KEY` | Секретный ключ Django |
| `DB_PASSWORD` | Пароль PostgreSQL |
| `OPENROUTER_API_KEY` | API-ключ [OpenRouter](https://openrouter.ai/) |
| `EMAIL_PROVIDER` | `smtp` (Yandex) или `resend` |
| `EMAIL_ADMIN` | Email, куда приходят заявки |
| `SEND_USER_EMAIL_COPY` | Копия пользователю (`True` / `False`) |
| `EMAIL_HOST_USER` | Yandex-логин (при `smtp`) |
| `EMAIL_HOST_PASSWORD` | Пароль приложения Yandex |
| `DEFAULT_FROM_EMAIL` | Адрес отправителя |

**Группа 2 — дефолты для Docker (менять не обязательно):**

`DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_HOST=db`, `DB_PORT`, `REDIS_HOST=redis`, `REDIS_PORT`, модели OpenRouter, настройки SMTP, CORS, rate limit.

### Установка зависимостей и запуск

Зависимости устанавливаются **автоматически** при сборке Docker-образа (`requirements.txt`).

```bash
# 1. Заполните секреты в .env.example
# 2. Запуск
docker compose up --build
```

Приложение: **http://localhost:8000**  
API: **http://localhost:8000/api/**  
Swagger: **http://localhost:8000/api/docs/**

### Остановка

```bash
docker compose down -v --rmi all
```

Удаляет контейнеры, volumes (БД, логи) и собранные образы.

---

## 2. Стек технологий

### Backend

| Компонент | Технология |
|-----------|------------|
| Язык | Python 3.12 |
| Фреймворк | Django 6, Django REST Framework |
| БД | PostgreSQL 18 |
| Кеш | Redis 8 (django-redis) |
| HTTP-клиент | httpx |
| Санитизация | bleach |
| Конфигурация | django-environ |
| CORS | django-cors-headers |
| Документация API | drf-spectacular (OpenAPI / Swagger) |
| Сервер | Gunicorn + WhiteNoise |
| Контейнеризация | Docker, Docker Compose |

### AI

| Инструмент | Назначение |
|------------|------------|
| [OpenRouter API](https://openrouter.ai/) | Единый доступ к LLM (основная и резервная модель) |
| Rule-based fallback | Классификация по ключевым словам, если AI недоступен |

### Email

| Провайдер | Режим |
|-----------|-------|
| Yandex SMTP | `EMAIL_PROVIDER=smtp` — полная отправка (в Docker) |
| Resend API | `EMAIL_PROVIDER=resend` — используется на Render |

---

## 3. Архитектура

### Структура проекта

```
ai-messages-api/
├── config/                 # Настройки Django, URLs, WSGI
├── contact/
│   ├── middleware/         # Логирование запросов, rate limit
│   ├── services/           # Бизнес-логика, AI, email
│   ├── repositories/       # Работа с БД
│   ├── serializers/        # Валидация API
│   ├── exceptions/         # Обработка ошибок
│   ├── templates/          # Email-шаблоны, лендинг
│   └── tests/
├── static/                 # Bootstrap, статика лендинга
├── Dockerfile
├── docker-compose.yml
├── .env.example            # Переменные окружения
├── requirements.txt
└── render.yaml             # Blueprint для Render
```

### Паттерны проектирования

```
Controller (views.py)
    ↓
Service (contact_service, ai_service, email_service)
    ↓
Repository (contact_repository, log_repository)
    ↓
Model (PostgreSQL)
```

- **Слоистая архитектура** — разделение HTTP, бизнес-логики и доступа к данным
- **Repository** — инкапсуляция запросов к БД
- **Graceful degradation** — цепочка fallback для AI и email
- **Middleware** — cross-cutting concerns (логи, rate limit)

### Выбор технологий

| Решение | Почему |
|---------|--------|
| Django + DRF | Быстрая разработка REST API, встроенная админка, экосистема |
| PostgreSQL | Надёжное хранение обращений и логов |
| Redis | Rate limiting и кеш AI-ответов с TTL |
| OpenRouter | Доступ к нескольким LLM через один API, бесплатные модели |
| Docker Compose | Одинаковое окружение (web + db + redis) без ручной установки |
| drf-spectacular | Автогенерация OpenAPI-документации |

---

## 4. Реализация API

### Эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| `POST` | `/api/contact` | Отправка формы обратной связи |
| `GET` | `/api/health` | Проверка БД и Redis |
| `GET` | `/api/metrics` | Статистика обращений |
| `GET` | `/api/docs/` | Swagger UI |

### POST /api/contact

**Запрос:**

```bash
curl -X POST http://localhost:8000/api/contact \
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
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Обращение получено и будет обработано.",
  "ai_sentiment": "positive",
  "ai_category": "collaboration",
  "ai_reply": "Спасибо за интерес! Свяжусь с вами в ближайшее время.",
  "ai_used": true
}
```

### GET /api/health

**Ответ (200):**

```json
{
  "status": "ok",
  "checks": {
    "database": true,
    "redis": true
  }
}
```

### GET /api/metrics

**Ответ (200):**

```json
{
  "total_requests": 42,
  "by_category": {
    "bug": 5,
    "feature": 8,
    "collaboration": 12,
    "question": 10,
    "spam": 3,
    "general": 4
  },
  "by_sentiment": {
    "positive": 20,
    "neutral": 18,
    "negative": 4
  },
  "ai_processed": 38,
  "ai_fallback": 4,
  "spam_detected": 3
}
```

### Валидация

| Поле | Правила |
|------|---------|
| `name` | 2–100 символов, санитизация (bleach) |
| `phone` | Формат телефона (regex) |
| `email` | Валидный email |
| `comment` | 10–2000 символов |
| `website` | Honeypot — если заполнено, запрос отклоняется (400) |

### Обработка ошибок

| HTTP | `error` | Когда |
|------|---------|-------|
| 400 | `validation_error` | Невалидные данные |
| 429 | `rate_limit_exceeded` | Превышен лимит запросов с IP |
| 502 | `email_delivery_failed` | Ошибка отправки email |
| 500 | `internal_error` | Необработанное исключение |

**Пример ошибки валидации (400):**

```json
{
  "error": "validation_error",
  "message": "Ошибка валидации данных.",
  "details": {
    "name": ["Имя должно содержать минимум 2 символа."]
  }
}
```

---

## 5. AI-интеграция

### Инструменты и задачи

Один запрос к OpenRouter выполняет три задачи:

1. **Анализ тональности** — `positive` / `neutral` / `negative`
2. **Классификация** — `bug` / `feature` / `collaboration` / `question` / `spam` / `general`
3. **Генерация ответа** — черновик персонального ответа на русском

Модели задаются переменными `OPENROUTER_MODEL` и `OPENROUTER_FALLBACK_MODEL`.

### Fallback-цепочка

```
1. Основная модель (OPENROUTER_MODEL)
       ↓ ошибка
2. Резервная модель (OPENROUTER_FALLBACK_MODEL)
       ↓ ошибка
3. Rule-based классификатор (ключевые слова в комментарии)
```

Rule-based fallback помечается `ai_used: false`. Спам по ключевым словам (`купить`, `реклам`, `казино` и т.д.) не отправляет email.

### System prompt

```
Ты — ассистент backend-сервиса обратной связи разработчика.
Проанализируй обращение пользователя и верни ТОЛЬКО валидный JSON без markdown:
{
  "sentiment": "positive|neutral|negative",
  "category": "bug|feature|collaboration|question|spam|general",
  "reply": "вежливый персональный ответ на русском, 2-4 предложения"
}
Правила:
- sentiment: эмоциональный тон комментария
- category: тип запроса (spam — если реклама, бессмыслица, оскорбления)
- reply: черновик ответа от имени разработчика, без обещаний которые нельзя выполнить
```

User message: `Имя: {name}\nКомментарий: {comment}`

### Кеширование

Результаты AI кешируются в Redis на **1 час** по хешу комментария — повторные одинаковые обращения не расходуют API.

---

6. Использование ИИ в разработке

### Части, сгенерированные ИИ

- Docker
- Документация
- Типовой Django-код: middleware rate limit, repository, serializers с валидацией, exception handler

### Самостоятельная реализация

- Бизнес-логика
- Модели
- Категории
- Выбор стека
- rule-based fallback
- Промпты
- honeypot

### Использованные промпты

- README по требованиям: запуск, API, AI, хранение данных
- Docker: web + postgres + redis, секреты из .env.example
- Добавь rate limiting через Redis и логирование запросов

### Ручное исправление

- Неправильные версии redis и postgresql в Docker
- Некоторые части документации (как эта, например)
- Приведение к единому формату ошибок
- для ValidationError вручную добавил код validation_error, общее сообщение и поле details с ошибками по полям
- для необработанных исключений добавил JsonResponse с internal_error вместо HTML-страницы Django

---

## 7. Хранение данных

### Логи

| Тип | Где | Описание |
|-----|-----|----------|
| HTTP-запросы к `/api/*` | PostgreSQL (`RequestLog`) + `logs/requests.log` | method, path, status, IP, duration, user-agent |
| App-логи | `logs/app.log` | Django, contact, AI, email (ротация 5 МБ, 3 файла) |
| PII | Маскируется | Email и телефон в логах не выводятся целиком |

Middleware `RequestLoggingMiddleware` пишет каждый API-запрос в БД и файл.

### Rate limiting

- **Где:** Redis (ключ `ratelimit:{ip}`)
- **Лимит:** 5 POST-запросов за 900 секунд (15 мин) с одного IP
- **Где применяется:** `/api/contact` и форма на лендинге
- **При превышении:** HTTP 429, `rate_limit_exceeded`
- **Middleware:** `RateLimitMiddleware`

### Статистика

- **Эндпоинт:** `GET /api/metrics`
- **Источник:** PostgreSQL, таблица `ContactRequest`
- **Данные:** общее число обращений, разбивка по категориям и тональности, счётчики AI/fallback, количество спама

---

## Деплой (Render)

На production используется `EMAIL_PROVIDER=resend`. Без платного домена Resend отправляет письма только владельцу (`SEND_USER_EMAIL_COPY=False`). Полный функционал email доступен в Docker с `EMAIL_PROVIDER=smtp`.
