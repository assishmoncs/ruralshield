import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "lambda"))

import handler

CLIENT_ID = "8a1243b7-3c8f-4ab7-91f4-37e251d621f4"


def event(method, path, headers=None, body=None):
    return {
        "requestContext": {"http": {"method": method, "path": path}},
        "headers": headers or {},
        "body": json.dumps(body) if body is not None else None,
    }


def authenticated_event(method, path, subject="user-123", headers=None, body=None):
    request = event(method, path, headers, body)
    request["requestContext"]["authorizer"] = {"jwt": {"claims": {"sub": subject}}}
    return request


def test_history_rejects_missing_authenticated_identity():
    response = handler.lambda_handler(event("GET", "/history"), None)
    assert response["statusCode"] == 401


def test_browser_client_id_cannot_authorize_history():
    response = handler.lambda_handler(
        event("GET", "/history", {"x-ruralshield-client-id": CLIENT_ID}), None
    )
    assert response["statusCode"] == 401


def test_history_is_scoped_to_authenticated_subject(monkeypatch):
    seen = {}

    def fake_history(owner_id, limit):
        seen["owner_id"] = owner_id
        seen["limit"] = limit
        return []

    monkeypatch.setattr(handler, "list_history", fake_history)
    response = handler.lambda_handler(authenticated_event("GET", "/history"), None)
    assert response["statusCode"] == 200
    assert seen == {"owner_id": "user#user-123", "limit": 50}


def test_jwt_subject_is_only_private_owner_identity():
    request = authenticated_event(
        "GET", "/history", headers={"x-ruralshield-client-id": CLIENT_ID}
    )
    assert handler._owner_id(request) == "user#user-123"


def test_anonymous_scan_remains_allowed_but_is_not_persisted(monkeypatch):
    seen = {}

    def fake_save(record):
        seen["owner_id"] = record["owner_id"]
        return record["owner_id"] != "anonymous"

    monkeypatch.setattr(handler, "save_scan", fake_save)
    response = handler.lambda_handler(
        event("POST", "/scan", body={"type": "message", "text": "Hello from my bank"}),
        None,
    )
    assert response["statusCode"] == 200
    assert seen["owner_id"] == "anonymous"
    assert json.loads(response["body"])["persisted"] is False


def test_api_responses_include_defensive_headers():
    response = handler.lambda_handler(event("GET", "/health"), None)
    headers = response["headers"]
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "no-referrer"
