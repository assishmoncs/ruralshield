# RuralShield Architecture Decisions

## ADR-001: Keep the security decision deterministic

**Decision:** The final phishing classification is produced from ML, rules, and passive URL evidence. Amazon Bedrock is not trusted as the security authority.

**Why:** Generative models are probabilistic and can produce inconsistent scores. Keeping the security decision deterministic makes the system easier to test, reason about, and fail safely. Bedrock remains valuable for contextual explanations and user-friendly recommendations.

## ADR-002: Analyze URLs passively

**Decision:** RuralShield parses and scores submitted URLs without making outbound HTTP requests to them.

**Why:** Automatically fetching attacker-controlled URLs would introduce unnecessary SSRF, redirect, DNS, and content-processing risk. Structural URL analysis is sufficient for the educational prototype.

## ADR-003: Keep anonymous scanning available

**Decision:** `/scan` remains publicly usable so users can quickly check a suspicious message. Anonymous requests are not persisted, and Bedrock inference for anonymous requests is disabled by default.

**Why:** A safety tool should have a low-friction entry point, but public access should not create an uncontrolled paid-AI endpoint. Authenticated users can unlock private history, feedback, and Bedrock explanations.

## ADR-004: Use Cognito ID tokens for user-owned APIs

**Decision:** The frontend sends the Cognito ID token as the bearer token for `/history`, `/statistics`, and `/feedback`. The backend additionally requires the `token_use=id` claim when deriving the DynamoDB owner identity.

**Why:** API Gateway HTTP API JWT authorization validates the token audience. Cognito ID tokens carry an `aud` claim for the app client, while access tokens use different claims intended for authorization/scopes. The backend therefore treats only an ID token as a private-record identity.

## ADR-005: Store derived scan metadata, not raw message bodies

**Decision:** Scan records contain the classification, scores, reasons, language, category, URL domain, model version, and a sanitized hash instead of the original message text.

**Why:** Phishing messages may contain credentials or personal information. Data minimization reduces the impact of an accidental disclosure while keeping enough metadata for history and analytics.

## ADR-006: Keep the bundled dataset intentionally small and deterministic

**Decision:** The repository ships a synthetic 40-row dataset for CI and demos while providing a reproducible preparation script for a larger licensed public SMS phishing corpus.

**Why:** CI should not depend on downloading third-party data or redistributing data whose terms are unclear. Production-style performance claims require a larger representative dataset and a separately documented model release.

## ADR-007: Use a lightweight pure-Python ML runtime

**Decision:** The Lambda inference implementation uses a serialized TF-IDF + logistic-regression model with standard-library inference instead of shipping the full scikit-learn stack.

**Why:** This keeps the Lambda package small and reduces cold-start/dependency complexity. Training remains reproducible locally; the trade-off is that more advanced NLP and multilingual modeling require a future model/runtime change.
