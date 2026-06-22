FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY manage.py build.sh ./
COPY config/ config/
COPY contact/ contact/
COPY static/ static/

EXPOSE 8000

CMD ["sh", "-c", "python manage.py collectstatic --no-input && python manage.py migrate --no-input && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120"]
