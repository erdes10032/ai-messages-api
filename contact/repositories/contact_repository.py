from contact.models import ContactRequest


class ContactRepository:
    def create(
        self,
        *,
        name: str,
        phone: str,
        email: str,
        comment: str,
        client_ip: str | None,
        ai_sentiment: str,
        ai_category: str,
        ai_reply: str,
        ai_used: bool,
    ) -> ContactRequest:
        return ContactRequest.objects.create(
            name=name,
            phone=phone,
            email=email,
            comment=comment,
            client_ip=client_ip,
            ai_sentiment=ai_sentiment,
            ai_category=ai_category,
            ai_reply=ai_reply,
            ai_used=ai_used,
        )

    def get_metrics(self) -> dict:
        total = ContactRequest.objects.count()
        by_category = {}
        for value, label in ContactRequest.Category.choices:
            by_category[value] = ContactRequest.objects.filter(ai_category=value).count()

        by_sentiment = {
            value: ContactRequest.objects.filter(ai_sentiment=value).count()
            for value, _ in ContactRequest.Sentiment.choices
        }

        ai_used_count = ContactRequest.objects.filter(ai_used=True).count()
        spam_count = ContactRequest.objects.filter(ai_category=ContactRequest.Category.SPAM).count()

        return {
            'total_requests': total,
            'by_category': by_category,
            'by_sentiment': by_sentiment,
            'ai_processed': ai_used_count,
            'ai_fallback': total - ai_used_count,
            'spam_detected': spam_count,
        }
