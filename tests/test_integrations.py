import json
import sys
from decimal import Decimal
from pathlib import Path

from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "lambda"))

import bedrock_service
import storage


class FakeTable:
    def __init__(self, items=None, pages=None):
        self.items = list(items or [])
        self.pages = list(pages or [])
        self.put_items = []
        self.queries = []

    def put_item(self, Item):
        self.put_items.append(Item)
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def query(self, **kwargs):
        self.queries.append(kwargs)
        if self.pages:
            return self.pages.pop(0)
        return {"Items": self.items[: kwargs["Limit"]]}


class FakeBedrockClient:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return {"output": {"message": {"content": [{"text": self.text}]}}}


def aws_error(operation):
    return ClientError({"Error": {"Code": "AccessDeniedException", "Message": "denied"}}, operation)


def test_dynamodb_save_converts_float_to_decimal(monkeypatch):
    table = FakeTable()
    monkeypatch.setattr(storage, "_table", lambda: table)
    assert storage.save_scan({"owner_id": "user#abc", "scan_key": "t#abc", "risk_score": 81.25}) is True
    assert table.put_items[0]["risk_score"] == Decimal("81.25")


def test_anonymous_scan_is_not_persisted(monkeypatch):
    table = FakeTable()
    monkeypatch.setattr(storage, "_table", lambda: table)
    assert storage.save_scan({"owner_id": "anonymous", "scan_key": "t#abc"}) is False
    assert table.put_items == []


def test_dynamodb_history_uses_owner_query_without_raw_message(monkeypatch):
    table = FakeTable([
        {"scan_id": "new", "timestamp": "2026-02-01T00:00:00+00:00"},
        {"scan_id": "old", "timestamp": "2026-01-01T00:00:00+00:00"},
    ])
    monkeypatch.setattr(storage, "_table", lambda: table)
    rows = storage.list_history("user#private", 10)
    assert [row["scan_id"] for row in rows] == ["new", "old"]
    assert table.queries[0]["ScanIndexForward"] is False
    assert all("text" not in row and "raw_message" not in row for row in rows)


def test_statistics_paginate_complete_owner_history(monkeypatch):
    table = FakeTable(pages=[
        {
            "Items": [{"classification": "PHISHING", "scam_category": "OTP Scam"}],
            "LastEvaluatedKey": {"owner_id": "user#private", "scan_key": "page1"},
        },
        {
            "Items": [{"classification": "SAFE", "scam_category": "Other/Unknown"}],
        },
    ])
    monkeypatch.setattr(storage, "_table", lambda: table)
    result = storage.statistics("user#private")
    assert result["total_scans"] == 2
    assert result["phishing"] == 1
    assert result["safe"] == 1
    assert result["statistics_truncated"] is False
    assert len(table.queries) == 2
    assert "ExclusiveStartKey" in table.queries[1]


def test_dynamodb_factory_failure_degrades_cleanly(monkeypatch):
    def fail_table():
        raise aws_error("DescribeTable")

    monkeypatch.setattr(storage, "_table", fail_table)
    assert storage.save_scan({"owner_id": "user#abc", "scan_key": "t#abc"}) is False
    assert storage.list_history("user#abc", 10) == []


def test_bedrock_structured_response_is_validated(monkeypatch):
    payload = {"summary": "This message may be pretending to be your bank.", "reasons": ["It asks for an OTP"], "recommended_action": "Use the official bank app instead.", "scam_category": "OTP Scam", "ai_risk_score": 91}
    client = FakeBedrockClient(json.dumps(payload))
    monkeypatch.setattr(bedrock_service, "BEDROCK_MODEL_ID", "test-model")
    import boto3
    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: client)
    result = bedrock_service.analyze("Share [REDACTED] now", 80, 40, [{"rule_id": "OTP_REQUEST", "reason": "Requests an OTP"}], "en", [])
    assert result["available"] is True
    assert result["ai_risk_score"] == 91
    assert result["scam_category"] == "OTP Scam"
    request = client.calls[0]
    assert request["modelId"] == "test-model"
    assert "untrusted data" in request["system"][0]["text"]


def test_bedrock_malformed_json_falls_back(monkeypatch):
    client = FakeBedrockClient("not-json")
    monkeypatch.setattr(bedrock_service, "BEDROCK_MODEL_ID", "test-model")
    import boto3
    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: client)
    result = bedrock_service.analyze("urgent kyc", 70, 0, [{"rule_id": "FAKE_KYC", "reason": "Uses KYC verification pressure"}], "en", [])
    assert result["available"] is False
    assert result["scam_category"] == "KYC Scam"
    assert result["recommended_action"]
