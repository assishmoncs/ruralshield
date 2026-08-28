from urllib.parse import urlparse

from config import MAX_TEXT_LENGTH

ALLOWED_TYPES = {"message", "url"}
ALLOWED_FIELDS = {"type", "text", "language"}


def validate_scan_payload(payload):
    if not isinstance(payload, dict):
        raise TypeError("Request body must be a JSON object")
    unknown = set(payload) - ALLOWED_FIELDS
    if unknown:
        raise ValueError(f"Unexpected fields: {', '.join(sorted(unknown))}")
    input_type = payload.get("type")
    text = payload.get("text")
    if input_type not in ALLOWED_TYPES:
        raise ValueError("type must be 'message' or 'url'")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text is required")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"text exceeds {MAX_TEXT_LENGTH} characters")
    if input_type == "url":
        parsed = urlparse(text.strip() if "://" in text else "https://" + text.strip())
        if not parsed.hostname:
            raise ValueError("Malformed URL")
    language = payload.get("language")
    if language is not None and (not isinstance(language, str) or len(language) > 12):
        raise ValueError("Invalid language")
    return {"type": input_type, "text": text.strip(), "language": language}
