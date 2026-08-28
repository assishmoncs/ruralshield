# API

Base URL is the `ApiUrl` output from the SAM stack.

## POST /scan
Content-Type: `application/json`

Message request:
```json
{"type":"message","text":"Your account will be blocked...","language":"en"}
```
URL request:
```json
{"type":"url","text":"https://example.invalid/login","url":"https://example.invalid/login","language":"en"}
```
The response includes `classification`, `risk_score`, `confidence`, `scam_category`, `reasons`, `recommendation`, `detected_language`, and analysis metadata. Invalid/oversized requests return a 4xx response. Internal service errors are sanitized.

## GET /history
Returns recent sanitized scan records. Raw message content is not part of the intended storage contract.

## GET /statistics
Returns counts computed from stored scan records: total, safe, suspicious, phishing, phishing percentage and category counts. Values are not synthetic.

## CORS
Configure `AllowedOrigin` at deployment to the exact frontend origin. The infrastructure template deliberately avoids a wildcard production origin.