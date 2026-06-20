# Generated manually for initial schema

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ContactRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=20)),
                ('email', models.EmailField(max_length=254)),
                ('comment', models.TextField(max_length=2000)),
                ('ai_sentiment', models.CharField(
                    choices=[
                        ('positive', 'Позитивный'),
                        ('neutral', 'Нейтральный'),
                        ('negative', 'Негативный'),
                        ('unknown', 'Не определён'),
                    ],
                    default='unknown',
                    max_length=20,
                )),
                ('ai_category', models.CharField(
                    choices=[
                        ('bug', 'Ошибка / баг'),
                        ('feature', 'Предложение'),
                        ('collaboration', 'Сотрудничество'),
                        ('question', 'Вопрос'),
                        ('spam', 'Спам'),
                        ('general', 'Общее обращение'),
                        ('unknown', 'Не определён'),
                    ],
                    default='unknown',
                    max_length=20,
                )),
                ('ai_reply', models.TextField(blank=True, default='')),
                ('ai_used', models.BooleanField(default=False)),
                ('client_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'verbose_name': 'Обращение',
                'verbose_name_plural': 'Обращения',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RequestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.CharField(max_length=10)),
                ('path', models.CharField(max_length=255)),
                ('status_code', models.PositiveSmallIntegerField()),
                ('client_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('duration_ms', models.PositiveIntegerField()),
                ('user_agent', models.CharField(blank=True, default='', max_length=512)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'verbose_name': 'Лог запроса',
                'verbose_name_plural': 'Логи запросов',
                'ordering': ['-created_at'],
            },
        ),
    ]
