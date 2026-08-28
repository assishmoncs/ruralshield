# RuralShield API

The API is a small HTTP API behind Amazon API Gateway and AWS Lambda. Scan requests are public so a user can check a message before signing in; personal history, statistics, and feedback are authenticated with a Cognito JWT authorizer.

## POST /scan

Analyze a message or URL.

Headers:

```http
Content-Type: application/json
```

Message request:

```json
{
  "type": "message",
  "text": "URGENT: Your KYC expires today. Do not share your OTP...",
  "language": "en"
}
```

URL request:

```json
{
  "type": "url",
  "text": "https://example.invalid/login",
  "language": "en"
}
```

Supported input types: `message`, `url`.
Supported languages: `en`, `hi`, `ta`.

The response includes:

- `classification`: `SAFE`, `SUSPICIOUS`, or `PHISHING`
- `risk_score`: deterministic 0–100 risk score
- `confidence_level`: qualitative decision strength (`LOW`, `MEDIUM`, `HIGH`), not a calibrated probability
- `model_version`
- `scam_category`
- `reasons`
- `recommendation`
- `detected_language`
- `components`: ML, URL, rule, and AI observability scores
- `decision_basis`: currently `ml_rules_url`
- `ai_used_for_decision`: always `false`
- `url_analysis`: passive structural analysis
- `mitigating_signals`
- `bedrock_available`

The security decision uses ML + rules + passive URL evidence. Amazon Bedrock is a contextual explanation layer and does not control the final classification.

Invalid or oversized requests return HTTP 400. Protected endpoints return HTTP 401 without a valid Cognito JWT. Internal service errors are sanitized for clients.

## GET /history

**Authentication required.** Returns recent sanitized scan records belonging only to the authenticated user. Raw message content is not part of the storage contract.

## GET /statistics

**Authentication required.** Returns counts computed from that user's stored scan records, including total, safe, suspicious, phishing, phishing percentage, and category counts.

## POST /feedback

**Authentication required.** Records whether the result was useful or incorrect for the authenticated user's scan.

Request:

```json
{
  "scan_id": "123e4567-e89b-12d3-a456-426614174000",
  "feedback": "helpful"
}
```

Allowed feedback values: `helpful`, `incorrect`.

The backend verifies that the target scan belongs to the authenticated user before updating it.

## GET /health

Public liveness endpoint.

Example response:

```json
{
  "status": "ok",
  "service": "RuralShield AI"
}
```

## CORS

Configure `AllowedOrigin` at deployment to the exact HTTPS frontend origin. Avoid wildcard origins for production-style deployments.

## Privacy

Never submit real OTPs, PINs, passwords, or complete card details. Submitted content is sanitized before downstream AI/persistence where practical, and the database stores derived metadata rather than the raw message body.
