import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "lambda"))

from config import MAX_TEXT_LENGTH
from handler import lambda_handler
from language import detect_language
from sanitizer import sanitize_text
from url_analyzer import analyze_url
from validators import validate_scan_payload


def post_scan(payload):
    event = {
        "requestContext": {"http": {"method": "POST", "path": "/scan"}},
        "body": json.dumps(payload, ensure_ascii=False),
    }
    return lambda_handler(event, None)


def test_oversized_message_is_rejected():
    with pytest.raises(ValueError):
        validate_scan_payload({"type": "message", "text": "x" * (MAX_TEXT_LENGTH + 1)})


def test_api_rejects_oversized_message():
    response = post_scan({"type": "message", "text": "x" * (MAX_TEXT_LENGTH + 1)})
    assert response["statusCode"] == 400


def test_malformed_url_is_rejected():
    with pytest.raises(ValueError):
        validate_scan_payload({"type": "url", "text": "http://[invalid"})


def test_unicode_url_is_analyzed_passively():
    result = analyze_url("https://उदाहरण.भारत/login")
    assert result["features"]["https"] is True
    assert result["features"]["hostname"]


def test_multiple_urls_use_highest_risk_signal():
    text = "Check https://example.org and http://192.0.2.10/verify"
    response = post_scan({"type": "message", "text": text})
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body["url_analysis"]["urls_checked"] == 2
    assert body["url_analysis"]["features"]["hostname"] == "192.0.2.10"
    assert body["url_analysis"]["features"]["ip_host"] is True


def test_mixed_language_detection_returns_supported_code():
    language = detect_language("आपका bank account सुरक्षित है")
    assert isinstance(language, str)
    assert language


def test_sanitizer_does_not_persist_obvious_card_secret():
    output = sanitize_text("Card 4111 1111 1111 1111, OTP 123456")
    assert "4111 1111 1111 1111" not in output
    assert "123456" not in output


def test_legitimate_urgent_message_still_returns_explanation():
    response = post_scan(
        {
            "type": "message",
            "text": (
                "Urgent security notice: if you did not make this payment, "
                "open the official bank app or call the number on your card. "
                "Never share your OTP or PIN."
            ),
        }
    )
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body["classification"] in {"SAFE", "SUSPICIOUS", "PHISHING"}
    assert body["reasons"]
    assert body["recommendation"]


def test_invalid_input_type_is_rejected_by_api():
    response = post_scan({"type": "attachment", "text": "hello"})
    assert response["statusCode"] == 400
