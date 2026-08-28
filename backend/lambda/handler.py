import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone

from bedrock_service import analyze as bedrock_analyze
from config import ALLOWED_ORIGINS, BEDROCK_PUBLIC_ACCESS
from language import detect_language
from ml_predictor import predict_risk
from risk_engine import combine_scores
from rules import evaluate_rules
from sanitizer import sanitize_text
from storage import list_history, save_feedback, save_scan, statistics
from url_analyzer import analyze_url
from validators import validate_feedback_payload, validate_scan_payload

logger = logging.getLogger()
logger.setLevel(logging.INFO)
URL_PATTERN = re.compile(r"(?i)\b((?:https?://|www\.)[^\s<>]+)")
MAX_URLS_PER_MESSAGE = 5


def _header(event, name):
    headers = event.get("headers") or {}
    return headers.get(name) or headers.get(name.lower()) or headers.get(name.title())


def _owner_id(event):
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    subject = claims.get("sub")
    return f"user#{subject}" if subject else "anonymous"


def _headers(event):
    origin = _header(event, "origin")
    allowed = origin if origin in ALLOWED_ORIGINS else (ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else "")
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": allowed,
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Cache-Control": "no-store",
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Vary": "Origin",
    }


def _response(event, status, body):
    return {"statusCode": status, "headers": _headers(event), "body": json.dumps(body, ensure_ascii=False, default=str)}


def _route(event):
    ctx = event.get("requestContext", {}).get("http", {})
    method = ctx.get("method") or event.get("httpMethod") or "GET"
    path = ctx.get("path") or event.get("path") or "/"
    return method.upper(), path


def _parse_json(event):
    try:
        return json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        raise ValueError("Malformed JSON") from None


def _extract_urls(text):
    urls = []
    for match in URL_PATTERN.finditer(text or ""):
        url = match.group(1).rstrip(".,);]")
        if url not in urls:
            urls.append(url)
        if len(urls) >= MAX_URLS_PER_MESSAGE:
            break
    return urls


def _analyze_urls(urls):
    if not urls:
        return {"score": 0, "features": {}, "reasons": [], "urls_checked": 0}
    analyses = [analyze_url(url) for url in urls]
    highest = max(analyses, key=lambda result: result["score"])
    reasons = []
    for result in analyses:
        for reason in result["reasons"]:
            if reason not in reasons:
                reasons.append(reason)
    return {
        "score": highest["score"],
        "features": {**highest["features"], "urls_checked": len(analyses)},
        "reasons": reasons[:8],
        "urls_checked": len(analyses),
    }


def _scan(event):
    try:
        payload = _parse_json(event)
    except ValueError as exc:
        return _response(event, 400, {"error": str(exc)})
    try:
        payload = validate_scan_payload(payload)
    except (TypeError, ValueError) as exc:
        return _response(event, 400, {"error": str(exc)})

    started = time.perf_counter()
    request_id = event.get("requestContext", {}).get("requestId") or str(uuid.uuid4())
    owner_id = _owner_id(event)
    sanitized = sanitize_text(payload["text"])
    language = payload.get("language") or detect_language(sanitized)
    urls = [payload["text"]] if payload["type"] == "url" else _extract_urls(payload["text"])
    url_result = _analyze_urls(urls)
    rule_result = evaluate_rules(sanitized)
    ml_result = predict_risk(sanitized)
    ai = bedrock_analyze(
        sanitized,
        ml_result["score"],
        url_result["score"],
        rule_result["hits"],
        language,
        url_result["reasons"],
        allow_bedrock=(owner_id != "anonymous" or BEDROCK_PUBLIC_ACCESS),
    )
    combined = combine_scores(
        ml_result["score"],
        url_result["score"],
        rule_result["score"],
        ai.get("ai_risk_score", 0),
        ml_available=ml_result.get("available", False),
        url_available=bool(urls),
        ai_available=ai.get("available", False),
    )

    reasons = []
    for item in [h["reason"] for h in rule_result["hits"]] + url_result["reasons"] + ai.get("reasons", []):
        if item and item not in reasons:
            reasons.append(item)
    if not reasons:
        reasons = ["No strong phishing signals were found in this scan."]

    recommendation = ai.get("recommended_action") or "Do not share your OTP, PIN, password, or card details. Contact your bank using an official channel if you are unsure."
    summary = ai.get("summary") or (
        "This looks high risk."
        if combined["classification"] == "PHISHING"
        else "This needs caution."
        if combined["classification"] == "SUSPICIOUS"
        else "No strong phishing signs were found."
    )
    host = url_result.get("features", {}).get("hostname") or ""
    scan_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "owner_id": owner_id,
        "scan_key": f"{timestamp}#{scan_id}",
        "scan_id": scan_id,
        "timestamp": timestamp,
        "input_type": payload["type"],
        "classification": combined["classification"],
        "risk_score": combined["risk_score"],
        "confidence_level": combined["confidence_level"],
        "detected_language": language,
        "scam_category": ai.get("scam_category", "Other/Unknown"),
        "reasons": reasons[:8],
        "url_domain": host,
        "triggered_rules": [h["rule_id"] for h in rule_result["hits"]],
        "model_version": ml_result.get("model_version", "unknown"),
    }
    persisted = save_scan(record)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    logger.info(
        json.dumps(
            {
                "request_id": request_id,
                "duration_ms": duration_ms,
                "classification": record["classification"],
                "risk_score": record["risk_score"],
                "bedrock_available": ai.get("available", False),
                "bedrock_access_mode": "enabled" if ai.get("available", False) else ai.get("fallback_reason", "disabled"),
                "persisted": persisted,
                "urls_checked": len(urls),
            }
        )
    )

    public_record = {key: value for key, value in record.items() if key not in {"owner_id", "scan_key"}}
    return _response(
        event,
        200,
        {
            **public_record,
            "summary": summary,
            "recommendation": recommendation,
            "components": combined["components"],
            "weights_used": combined["weights_used"],
            "decision_basis": combined["decision_basis"],
            "ai_used_for_decision": combined["ai_used_for_decision"],
            "url_analysis": {
                "score": url_result["score"],
                "reasons": url_result["reasons"],
                "features": url_result["features"],
                "urls_checked": url_result["urls_checked"],
            },
            "mitigating_signals": rule_result.get("mitigating_hits", []),
            "ml": ml_result,
            "bedrock_available": ai.get("available", False),
            "bedrock_fallback_reason": ai.get("fallback_reason"),
            "persisted": persisted,
        },
    )


def _feedback(event):
    owner_id = _owner_id(event)
    if owner_id == "anonymous":
        return _response(event, 401, {"error": "Authentication is required for feedback"})
    try:
        payload = validate_feedback_payload(_parse_json(event))
    except (TypeError, ValueError) as exc:
        return _response(event, 400, {"error": str(exc)})
    recorded = save_feedback(owner_id, payload["scan_id"], payload["feedback"])
    if not recorded:
        return _response(event, 404, {"error": "Scan not found for this user"})
    return _response(event, 200, {"success": True})


def lambda_handler(event, context):
    method, path = _route(event)
    if method == "OPTIONS":
        return _response(event, 204, {})
    if method == "POST" and path.endswith("/scan"):
        return _scan(event)
    if method == "POST" and path.endswith("/feedback"):
        return _feedback(event)
    if method == "GET" and path.endswith("/history"):
        owner_id = _owner_id(event)
        if owner_id == "anonymous":
            return _response(event, 401, {"error": "Authentication is required for history"})
        return _response(event, 200, {"items": list_history(owner_id, 50)})
    if method == "GET" and path.endswith("/statistics"):
        owner_id = _owner_id(event)
        if owner_id == "anonymous":
            return _response(event, 401, {"error": "Authentication is required for statistics"})
        return _response(event, 200, statistics(owner_id))
    if method == "GET" and (path == "/" or path.endswith("/health")):
        return _response(event, 200, {"status": "ok", "service": "RuralShield AI"})
    return _response(event, 404, {"error": "Not found"})
