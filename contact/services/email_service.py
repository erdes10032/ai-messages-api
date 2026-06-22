import logging

from django.conf import settings
from django.template.loader import render_to_string

from contact.models import ContactRequest
from contact.services.resend_client import ResendError, send_via_resend

logger = logging.getLogger('contact')


class EmailService:
    def send_contact_notifications(self, contact: ContactRequest) -> None:
        self._send_to_owner(contact)
        if settings.SEND_USER_EMAIL_COPY:
            self._send_copy_to_user(contact)

    def _send_email(
        self,
        *,
        to: str | list[str],
        subject: str,
        text_body: str,
        html_body: str,
        reply_to: str | None = None,
    ) -> None:
        if not settings.RESEND_API_KEY:
            raise ResendError('RESEND_API_KEY is not configured')

        send_via_resend(
            to=to,
            subject=subject,
            text=text_body,
            html=html_body,
            reply_to=reply_to,
        )

    def _send_to_owner(self, contact: ContactRequest) -> None:
        subject = f'[Обращение] {contact.get_ai_category_display()} — {contact.name}'
        context = {'contact': contact, 'is_owner': True}
        text_body = render_to_string('contact/emails/owner_notification.txt', context)
        html_body = render_to_string('contact/emails/owner_notification.html', context)

        self._send_email(
            to=settings.EMAIL_ADMIN,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            reply_to=contact.email,
        )
        logger.info('Owner notification sent for contact %s', contact.id)

    def _send_copy_to_user(self, contact: ContactRequest) -> None:
        subject = 'Ваше обращение получено'
        context = {'contact': contact, 'is_owner': False}
        text_body = render_to_string('contact/emails/user_copy.txt', context)
        html_body = render_to_string('contact/emails/user_copy.html', context)

        self._send_email(
            to=contact.email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )
        logger.info('User copy sent for contact %s', contact.id)
