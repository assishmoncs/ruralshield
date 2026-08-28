import hashlib
import re

CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
OTP_RE = re.compile(r"(?i)\b(?:otp|one[- ]?time password|pin)\s*(?:is|:|-)?\s*([0-9]{4,8})\b")
PASSWORD_RE = re.compile(r"(?i)\b(password|passcode)\s*(?:is|:|-)?\s*([^\s,.;]{4,})")
ACCOUNT_RE = re.compile(r"(?i)\b(account(?: number| no\.?| #)?)\s*(?:is|:|-)?\s*([0-9]{6,18})\b")


def sanitize_text(text: str) -> str:
    value = text or ""
    value = CARD_RE.sub("[REDACTED_CARD]", value)
    value = OTP_RE.sub(lambda m: m.group(0).replace(m.group(1), "[REDACTED_OTP]"), value)
    value = PASSWORD_RE.sub(lambda m: f"{m.group(1)} [REDACTED_SECRET]", value)
    value = ACCOUNT_RE.sub(lambda m: f"{m.group(1)} [REDACTED_ACCOUNT]", value)
    return value


def content_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
