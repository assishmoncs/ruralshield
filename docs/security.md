# Security & Privacy

## Threat model
RuralShield treats scan text and URLs as hostile input. Threats include oversized/malformed requests, prompt injection inside phishing text, secret leakage, malicious URLs, excessive IAM permissions, cross-origin abuse, sensitive logging and malformed AI output.

## Implemented controls
- Request validation and bounded input sizes.
- Secret/card/OTP-style redaction before downstream AI/persistence where practical.
- SHA-256 fingerprinting of sanitized text rather than persistence of raw messages.
- Passive URL parsing only; no server-side request is made to a submitted URL, preventing the analyzer from becoming an SSRF primitive.
- Bedrock is supplemental. Its response is parsed defensively and deterministic ML/rule/URL analysis remains usable when Bedrock is unavailable.
- The prompt explicitly frames submitted content as untrusted data, not instructions.
- API CORS origin is deployment-configurable; production should use the exact frontend origin.
- SAM grants DynamoDB access only to the project table and `bedrock:InvokeModel` only for the configured model ARN.
- No credentials or API keys are stored in source.
- CloudWatch-compatible logging should contain request IDs, durations, classification/risk and error categories, never raw submitted content or secrets.

## Data minimization
Stored scan records are intended to contain derived metadata: ID/time, input type, result, scores, language, scam category, reasons/rule IDs, URL domain and sanitized content hash. Raw message bodies are deliberately excluded.

## Deployment notes
S3 website hosting is suitable for a classroom/demo deployment but does not itself provide HTTPS. For a stronger public deployment, place CloudFront with HTTPS in front of a private S3 origin and update the allowed API origin. Authentication is intentionally not faked: if per-user private history is required, add Cognito (or another properly verified identity layer) and enforce ownership server-side before exposing user-specific history.

## Residual risks
Redaction is heuristic and cannot guarantee recognition of every secret. ML can misclassify novel scams. LLM explanations can be wrong. Structural URL analysis does not establish reputation or ownership. Treat RuralShield as decision support, not a guarantee.