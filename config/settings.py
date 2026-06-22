"""
Django settings for presentation-api project.
"""

from pathlib import Path
import sys

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    REDIS_USE_SSL=(bool, False),
    EMAIL_USE_SSL=(bool, False),
    EMAIL_USE_TLS=(bool, True),
    SEND_USER_EMAIL_COPY=(bool, True),
    RATE_LIMIT_REQUESTS=(int, 5),
    RATE_LIMIT_WINDOW_SECONDS=(int, 900),
    OPENROUTER_TIMEOUT_SECONDS=(int, 15),
)

environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'drf_spectacular',
    'contact',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'contact.middleware.request_logging.RequestLoggingMiddleware',
    'contact.middleware.rate_limit.RateLimitMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

if env('DATABASE_URL', default=None):
    DATABASES = {'default': env.db('DATABASE_URL')}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME'),
            'USER': env('DB_USER'),
            'PASSWORD': env('DB_PASSWORD'),
            'HOST': env('DB_HOST'),
            'PORT': env('DB_PORT'),
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }

if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_ROOT.mkdir(exist_ok=True)
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redis cache (rate limiting + AI response cache)
_redis_url = env('REDIS_URL', default=None)
if not _redis_url:
    _redis_scheme = 'rediss' if env('REDIS_USE_SSL') else 'redis'
    _redis_user = env('REDIS_USERNAME', default='')
    _redis_password = env('REDIS_PASSWORD', default='')
    _redis_host = env('REDIS_HOST', default='localhost')
    _redis_port = env('REDIS_PORT', default='6379')
    from urllib.parse import quote
    if _redis_password:
        _redis_url = (
            f'{_redis_scheme}://{_redis_user}:{quote(_redis_password)}'
            f'@{_redis_host}:{_redis_port}/0'
        )
    else:
        _redis_url = f'{_redis_scheme}://{_redis_host}:{_redis_port}/0'

REDIS_URL = _redis_url

_redis_options = {
    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    'SOCKET_CONNECT_TIMEOUT': 5,
    'SOCKET_TIMEOUT': 5,
    'IGNORE_EXCEPTIONS': True,
}
if env('REDIS_USE_SSL'):
    import ssl
    _redis_options['CONNECTION_POOL_KWARGS'] = {'ssl_cert_reqs': ssl.CERT_NONE}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': _redis_options,
        'KEY_PREFIX': 'presentation',
    }
}

if 'test' in sys.argv:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
        }
    }

# DRF
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'EXCEPTION_HANDLER': 'contact.exceptions.handlers.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [],
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Presentation API',
    'DESCRIPTION': 'Backend API для лендинг-презентации разработчика',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# CORS
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_METHODS = ['GET', 'POST', 'OPTIONS']
CORS_ALLOW_HEADERS = ['content-type', 'accept', 'origin']

# Email — переключение: smtp (Yandex) | resend
EMAIL_PROVIDER = env('EMAIL_PROVIDER', default='smtp')
EMAIL_ADMIN = env('EMAIL_ADMIN', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='')
SEND_USER_EMAIL_COPY = env('SEND_USER_EMAIL_COPY')
EMAIL_TIMEOUT = 15

# Yandex SMTP (EMAIL_PROVIDER=smtp)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.yandex.ru')
EMAIL_PORT = env.int('EMAIL_PORT', default=465)
EMAIL_USE_SSL = env('EMAIL_USE_SSL')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# Resend API (EMAIL_PROVIDER=resend)
RESEND_API_KEY = env('RESEND_API_KEY', default='')

# Rate limiting
RATE_LIMIT_REQUESTS = env('RATE_LIMIT_REQUESTS')
RATE_LIMIT_WINDOW_SECONDS = env('RATE_LIMIT_WINDOW_SECONDS')

# OpenRouter
OPENROUTER_API_KEY = env('OPENROUTER_API_KEY', default='')
OPENROUTER_MODEL = env('OPENROUTER_MODEL', default='openai/gpt-4o-mini')
OPENROUTER_FALLBACK_MODEL = env('OPENROUTER_FALLBACK_MODEL', default='google/gemini-flash-1.5')
OPENROUTER_TIMEOUT_SECONDS = env('OPENROUTER_TIMEOUT_SECONDS')

# Logging
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'requests_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'requests.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
        'contact': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'contact.requests': {
            'handlers': ['requests_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Security (production)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
