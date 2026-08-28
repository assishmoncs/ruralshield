import re
from urllib.parse import urlparse

from config import ALLOWED_LANGUAGES, MAX_TEXT_LENGTH

ALLOWED_TYPES = {"message", "url"}
ALLOWED_FIELDS = {"type", "text", "language"}
FEEDBACK_FIELDS = {"scan_id", "feedback"}
FEEDBACK_VALUES = {"helpful", "incorrect"}
SCAN_ID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


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
        candidate = text.strip() if "://" in text else "https://" + text.strip()
        parsed = urlparse(candidate)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Malformed URL")
    language = payload.get("language")
    if language is not None and (
        not isinstance(language, str) or language not in ALLOWED_LANGUAGES
    ):
        raise ValueError("Unsupported language")
    return {"type": input_type, "text": text.strip(), "language": language}


def validate_feedback_payload(payload):
    if not isinstance(payload, dict):
        raise TypeError("Request body must be a JSON object")
    unknown = set(payload) - FEEDBACK_FIELDS
    if unknown:
        raise ValueError(f"Unexpected fields: {', '.join(sorted(unknown))}")
    scan_id = payload.get("scan_id")
    feedback = payload.get("feedback")
    if not isinstance(scan_id, str) or not SCAN_ID_RE.fullmatch(scan_id):
        raise ValueError("scan_id must be a UUID")
    if feedback not in FEEDBACK_VALUES:
        raise ValueError("feedback must be 'helpful' or 'incorrect'")
    return {"scan_id": scan_id, "feedback": feedback}
