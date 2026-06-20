import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from contact.models import ContactRequest

logger = logging.getLogger('contact')


class EmailService:
    def send_contact_notifications(self, contact: ContactRequest) -> None:
        self._send_to_owner(contact)
        self._send_copy_to_user(contact)

    def _send_to_owner(self, contact: ContactRequest) -> None:
        subject = f'[Обращение] {contact.get_ai_category_display()} — {contact.name}'
        context = {'contact': contact, 'is_owner': True}
        text_body = render_to_string('contact/emails/owner_notification.txt', context)
        html_body = render_to_string('contact/emails/owner_notification.html', context)

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_ADMIN],
            reply_to=[contact.email],
        )
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=False)
        logger.info('Owner notification sent for contact %s', contact.id)

    def _send_copy_to_user(self, contact: ContactRequest) -> None:
        subject = 'Ваше обращение получено'
        context = {'contact': contact, 'is_owner': False}
        text_body = render_to_string('contact/emails/user_copy.txt', context)
        html_body = render_to_string('contact/emails/user_copy.html', context)

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[contact.email],
        )
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=False)
        logger.info('User copy sent for contact %s', contact.id)
