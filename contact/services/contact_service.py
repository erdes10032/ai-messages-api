import logging

from contact.exceptions.handlers import EmailDeliveryError
from contact.models import ContactRequest
from contact.repositories.contact_repository import ContactRepository
from contact.services.ai_service import AIService
from contact.services.email_service import EmailService

logger = logging.getLogger('contact')


class ContactService:
    def __init__(self):
        self._contact_repo = ContactRepository()
        self._ai_service = AIService()
        self._email_service = EmailService()

    def process_contact(
        self,
        *,
        name: str,
        phone: str,
        email: str,
        comment: str,
        client_ip: str | None,
    ) -> ContactRequest:
        ai_result = self._ai_service.analyze(name, comment)

        contact = self._contact_repo.create(
            name=name,
            phone=phone,
            email=email,
            comment=comment,
            client_ip=client_ip,
            ai_sentiment=ai_result.sentiment,
            ai_category=ai_result.category,
            ai_reply=ai_result.reply,
            ai_used=ai_result.ai_used,
        )

        if ai_result.category == ContactRequest.Category.SPAM:
            logger.warning('Spam detected for contact %s, skipping email', contact.id)
            return contact

        try:
            self._email_service.send_contact_notifications(contact)
        except Exception as exc:
            logger.exception('Failed to send emails for contact %s', contact.id)
            raise EmailDeliveryError() from exc

        return contact
