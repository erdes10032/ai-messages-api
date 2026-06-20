import hashlib
import re

import bleach

ALLOWED_TAGS: list[str] = []
ALLOWED_ATTRIBUTES: dict = {}

PHONE_PATTERN = re.compile(r'^\+?[\d\s\-()]{7,20}$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


def sanitize_text(value: str, max_length: int) -> str:
    cleaned = bleach.clean(value.strip(), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return cleaned[:max_length]


def is_valid_phone(phone: str) -> bool:
    digits = re.sub(r'\D', '', phone)
    return 7 <= len(digits) <= 15 and bool(PHONE_PATTERN.match(phone))


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email)) and len(email) <= 254


def mask_email(email: str) -> str:
    if '@' not in email:
        return '***'
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[0] + '***' + local[-1]
    return f'{masked_local}@{domain}'


def mask_phone(phone: str) -> str:
    digits = re.sub(r'\D', '', phone)
    if len(digits) < 4:
        return '***'
    return f'***{digits[-4:]}'


def get_client_ip(request) -> str | None:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def hash_for_cache(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
