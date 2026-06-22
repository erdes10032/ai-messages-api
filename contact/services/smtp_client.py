import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger('contact')


class SmtpError(Exception):
    pass


def send_via_smtp(
    *,
    to: str | list[str],
    subject: str,
    text: str,
    html: str,
    reply_to: str | None = None,
) -> None:
    if not settings.EMAIL_HOST_USER:
        raise SmtpError('EMAIL_HOST_USER is not configured')

    recipients = [to] if isinstance(to, str) else to
    message = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
        reply_to=[reply_to] if reply_to else None,
    )
    message.attach_alternative(html, 'text/html')

    try:
        message.send(fail_silently=False)
    except Exception as exc:
        logger.error('SMTP error: %s', exc)
        raise SmtpError(str(exc)) from exc

    logger.info('SMTP email sent to %s', recipients)
