from rest_framework import serializers

from contact.utils.sanitizers import is_valid_email, is_valid_phone, sanitize_text


class ContactSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, trim_whitespace=True)
    phone = serializers.CharField(max_length=20, trim_whitespace=True)
    email = serializers.EmailField(max_length=254)
    comment = serializers.CharField(max_length=2000, trim_whitespace=True)
    website = serializers.CharField(
        required=False, allow_blank=True, default='', write_only=True,
    )

    def validate_name(self, value: str) -> str:
        cleaned = sanitize_text(value, 100)
        if len(cleaned) < 2:
            raise serializers.ValidationError('Имя должно содержать минимум 2 символа.')
        return cleaned

    def validate_phone(self, value: str) -> str:
        cleaned = sanitize_text(value, 20)
        if not is_valid_phone(cleaned):
            raise serializers.ValidationError('Некорректный формат телефона.')
        return cleaned

    def validate_email(self, value: str) -> str:
        cleaned = value.strip().lower()
        if not is_valid_email(cleaned):
            raise serializers.ValidationError('Некорректный формат email.')
        return cleaned

    def validate_comment(self, value: str) -> str:
        cleaned = sanitize_text(value, 2000)
        if len(cleaned) < 10:
            raise serializers.ValidationError('Комментарий должен содержать минимум 10 символов.')
        return cleaned

    def validate(self, attrs: dict) -> dict:
        if attrs.get('website'):
            raise serializers.ValidationError(
                {'website': 'Spam detected.'},
                code='spam',
            )
        return attrs


class ContactResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    message = serializers.CharField()
    ai_sentiment = serializers.CharField()
    ai_category = serializers.CharField()
    ai_reply = serializers.CharField()
    ai_used = serializers.BooleanField()
