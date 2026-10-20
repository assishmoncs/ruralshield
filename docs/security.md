# Security & Privacy

## Scope and threat model

RuralShield AI is a research and educational prototype, not a certified banking fraud engine. It treats scan text and URLs as untrusted input. Relevant threats include malformed or oversized requests, phishing/social-engineering content, prompt injection, sensitive data exposure, malicious URLs, cross-origin abuse, excessive IAM permissions, and unexpected model output.

## Implemented controls

- **Input validation:** scan and feedback payloads are type-checked, reject unexpected fields, and enforce size and identifier constraints.
- **Data minimization:** the raw submitted message is not included in the saved scan record. The sanitizer redacts common OTP, password, account-number, and card-number patterns before sending text to Bedrock. Heuristic redaction is not guaranteed to recognize every secret.
- **Passive URL analysis:** the analyzer parses the submitted string locally. It does not issue HTTP requests to submitted URLs, so the scanner is not intended to act as a server-side URL fetcher. Malformed URL structures produce a bounded risk signal instead of being followed.
- **Deterministic decision authority:** the final risk score uses the active ML, rules, and URL signals. Amazon Bedrock provides optional contextual explanation and recommended actions; its generated score does not override the deterministic security verdict.
- **Prompt and output handling:** submitted content is framed as untrusted data in the Bedrock prompt. The response is parsed, category-checked, bounded, and handled with a local fallback when Bedrock is unavailable or responds unexpectedly.
- **Authenticated private routes:** API Gateway configures Cognito JWT authentication for history, statistics, and feedback. The Lambda handler derives the record owner from the verified ID-token claims, and storage operations are scoped to that owner.
- **AWS permissions and storage:** the Lambda role is scoped to the project DynamoDB table and configured Bedrock model. DynamoDB enables server-side encryption and point-in-time recovery. The S3 frontend bucket blocks public access and is served through CloudFront Origin Access Control.
- **Transport and browser controls:** CloudFront provides HTTPS for the frontend. The API CORS origin is deployment-configurable. API responses set no-store caching and defensive browser headers.
- **Logging:** scan logs capture request identifiers, duration, classification, risk score, persistence state, and service availability rather than the raw message body. Error logs avoid logging model response content or credentials.

## Data retention behavior

Anonymous scans can receive a verdict but are not saved as personal scan history. When a valid authenticated Cognito ID token is supplied, the application attempts to save derived scan metadata such as the result, scores, timestamp, input type, language, category, rule identifiers, and URL hostname. The raw message body is not part of that record. Persistence can fail independently of the detection response; the API reports whether the record was saved.

Do not submit a real OTP, PIN, password, full card number, or other confidential banking credential.

## Residual risks and deployment requirements

- The bundled ML dataset contains only 40 synthetic examples. The reported metrics are development checks, not evidence of production accuracy.
- URL features are structural heuristics and do not establish domain ownership, reputation, or malicious intent.
- Redaction is heuristic and can miss sensitive values or redact benign text.
- AI explanations may be incomplete or wrong and must remain secondary to the deterministic verdict.
- **Inference geography:** The configured APAC Nova Lite profile may route inference requests to supported Regions including Tokyo, Seoul, Osaka, Mumbai, Singapore, and Sydney. Sanitization is heuristic, so prompts are not guaranteed to remain in India; do not submit real credentials, and confirm this routing meets applicable data-residency requirements.
- Public deployment still requires live AWS smoke tests, cost and abuse monitoring, appropriate alarm thresholds, dependency maintenance, accessibility/usability review, and evaluation against a larger licensed real-world dataset.

RuralShield should be treated as decision support, not a guarantee that a message or URL is safe.
