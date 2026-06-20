import uuid

from django.db import models


class ContactRequest(models.Model):
    class Sentiment(models.TextChoices):
        POSITIVE = 'positive', 'Позитивный'
        NEUTRAL = 'neutral', 'Нейтральный'
        NEGATIVE = 'negative', 'Негативный'
        UNKNOWN = 'unknown', 'Не определён'

    class Category(models.TextChoices):
        BUG = 'bug', 'Ошибка / баг'
        FEATURE = 'feature', 'Предложение'
        COLLABORATION = 'collaboration', 'Сотрудничество'
        QUESTION = 'question', 'Вопрос'
        SPAM = 'spam', 'Спам'
        GENERAL = 'general', 'Общее обращение'
        UNKNOWN = 'unknown', 'Не определён'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(max_length=254)
    comment = models.TextField(max_length=2000)

    ai_sentiment = models.CharField(
        max_length=20, choices=Sentiment.choices, default=Sentiment.UNKNOWN,
    )
    ai_category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.UNKNOWN,
    )
    ai_reply = models.TextField(blank=True, default='')
    ai_used = models.BooleanField(default=False)

    client_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Обращение'
        verbose_name_plural = 'Обращения'

    def __str__(self):
        return f'{self.name} <{self.email}>'


class RequestLog(models.Model):
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    status_code = models.PositiveSmallIntegerField()
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField()
    user_agent = models.CharField(max_length=512, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Лог запроса'
        verbose_name_plural = 'Логи запросов'

    def __str__(self):
        return f'{self.method} {self.path} [{self.status_code}]'
