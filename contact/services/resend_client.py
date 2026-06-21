import logging

import httpx
from django.conf import settings

logger = logging.getLogger('contact')

RESEND_API_URL = 'https://api.resend.com/emails'


class ResendError(Exception):
    pass


def send_via_resend(
    *,
    to: str | list[str],
    subject: str,
    text: str,
    html: str,
    reply_to: str | None = None,
) -> None:
    if not settings.RESEND_API_KEY:
        raise ResendError('RESEND_API_KEY is not configured')

    recipients = [to] if isinstance(to, str) else to
    payload = {
        'from': settings.DEFAULT_FROM_EMAIL,
        'to': recipients,
        'subject': subject,
        'text': text,
        'html': html,
    }
    if reply_to:
        payload['reply_to'] = reply_to

    try:
        response = httpx.post(
            RESEND_API_URL,
            headers={
                'Authorization': f'Bearer {settings.RESEND_API_KEY}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=settings.EMAIL_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:500]
        logger.error('Resend API error %s: %s', exc.response.status_code, body)
        raise ResendError(f'Resend HTTP {exc.response.status_code}: {body}') from exc
    except httpx.HTTPError as exc:
        logger.error('Resend network error: %s', exc)
        raise ResendError(str(exc)) from exc

    logger.info('Resend email sent to %s', recipients)
