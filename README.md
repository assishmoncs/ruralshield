<div align="center">

<h1>🛡️ RuralShield AI</h1>

<p><strong>Privacy-first, explainable phishing-risk detection for rural banking users.</strong></p>

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12"/>
  <img src="https://img.shields.io/badge/AWS_Lambda-Serverless-FF9900?style=for-the-badge&logo=awslambda&logoColor=white" alt="AWS Lambda"/>
  <img src="https://img.shields.io/badge/Amazon_Bedrock-Generative_AI-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white" alt="Amazon Bedrock"/>
  <img src="https://img.shields.io/badge/DynamoDB-NoSQL-4053D6?style=for-the-badge&logo=amazondynamodb&logoColor=white" alt="DynamoDB"/>
  <img src="https://img.shields.io/badge/CloudFront-CDN-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white" alt="CloudFront"/>
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="MIT License"/>
  <img src="https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" alt="GitHub Actions CI"/>
</p>

<p>
  <img src="https://img.shields.io/badge/SDG_9-Industry_%26_Innovation-FD6925?style=flat-square" alt="SDG 9"/>
  <img src="https://img.shields.io/badge/SDG_10-Reduced_Inequalities-DD1367?style=flat-square" alt="SDG 10"/>
  <img src="https://img.shields.io/badge/SDG_1-No_Poverty-E5243B?style=flat-square" alt="SDG 1"/>
</p>

</div>

---

RuralShield AI is a fully serverless, mobile-first application that protects rural banking users from SMS/message phishing. It combines a custom-trained ML model, deterministic social-engineering rules, passive URL heuristics, and optional Amazon Bedrock generative AI context into a single, explainable risk score — all while storing **zero raw sensitive message data**.

> ⚠️ **Safety Notice:** Never enter a real OTP, PIN, password, or complete card number into RuralShield AI. This is a research and educational prototype, not a certified bank fraud engine. Detection is probabilistic.

---

## 📋 Table of Contents

- [What It Does](#-what-it-does)
- [Architecture](#️-architecture)
- [Tech Stack](#-tech-stack)
- [Detection Layers](#-detection-layers)
- [ML Model & Evaluation](#-ml-model--evaluation)
- [API Reference](#-api-reference)
- [Privacy Model](#-privacy-model)
- [Security Controls](#-security-controls)
- [Multilingual Support](#-multilingual-support)
- [Repository Layout](#-repository-layout)
- [Local Development](#-local-development)
- [AWS Deployment](#-aws-deployment)
- [CI / Quality Gate](#-ci--quality-gate)
- [SDG Alignment](#-sdg-alignment)
- [What "Production-Grade" Still Requires](#-what-production-grade-still-requires)

---

## 🎯 What It Does

`POST /scan` accepts a suspicious banking message or URL and returns a structured JSON result containing:

| Field | Description |
|---|---|
| `classification` | `SAFE`, `SUSPICIOUS`, or `PHISHING` |
| `risk_score` | 0–100 composite risk score |
| `confidence` | Calibrated confidence of the verdict |
| `reasons` | Human-readable list of triggered signals |
| `detected_language` | `en`, `hi`, or `ta` |
| `scam_category` | Categorized scam type (KYC, OTP, Loan, etc.) |
| `recommendation` | Plain-language safe action for the user |
| `components` | Individual scores from each detection layer |

> The LLM is **never the sole phishing authority**. Unavailable components are excluded and active detector weights are automatically renormalized. The system always returns a verdict.

---

## 🏛️ Architecture

```
                    Browser (Mobile-First SPA)
                            │ HTTPS
                            ▼
                     ┌─────────────┐
                     │ CloudFront  │  ── Signed OAC ──► Private S3 (Frontend)
                     └──────┬──────┘
                            │ HTTPS
                            ▼
                   ┌──────────────────┐
                   │  API Gateway     │  HTTP API  ·  Throttling  ·  CORS
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │  AWS Lambda      │  Python 3.12  ·  768 MB  ·  20s timeout
                   │  (Orchestrator)  │
                   └──┬───┬───┬───┬───┘
                      │   │   │   │
              ┌───────┘   │   │   └───────────────┐
              ▼           ▼   ▼                   ▼
        ┌──────────┐ ┌────────┐ ┌──────────┐ ┌──────────────┐
        │  TF-IDF  │ │ Rules  │ │   URL    │ │   Amazon     │
        │  Logistic│ │ Engine │ │ Analyzer │ │   Bedrock    │
        │ Regression│ │ (13   │ │(Passive/ │ │  Nova Lite   │
        │  (Custom)│ │ Rules) │ │Offline)  │ │  (Optional)  │
        └────┬─────┘ └───┬────┘ └────┬─────┘ └──────┬───────┘
             │           │          │               │
             └───────────┴──────────┴───────────────┘
                                   │
                          ┌────────▼────────┐
                          │  Risk Fusion    │  Weighted aggregation
                          │  Engine         │  + renormalization
                          └────────┬────────┘
                                   │
                     ┌─────────────┴──────────────┐
                     ▼                            ▼
             ┌───────────────┐          ┌──────────────────┐
             │  API Response │          │    DynamoDB      │
             │  (No raw msg) │          │ (Derived metadata│
             └───────────────┘          │  only · PITR on) │
                                        └──────────────────┘
                                                 │
                                        ┌────────▼────────┐
                                        │   CloudWatch    │
                                        │   Logs (14d)    │
                                        └─────────────────┘
```

The S3 origin is **private** and CloudFront uses **Origin Access Control (OAC)** with SigV4-signed requests. The API **never fetches submitted URLs**, completely eliminating SSRF attack surface.

---

## 🛠️ Tech Stack

### ☁️ AWS Services

| Service | Role |
|---|---|
| **AWS Lambda** | Serverless compute; Python 3.12 runtime, 768 MB memory |
| **Amazon API Gateway HTTP API** | REST-like HTTP routing with throttling (10 RPS, 20 burst) |
| **Amazon DynamoDB** | Serverless NoSQL persistence; PAY_PER_REQUEST billing; SSE + PITR enabled |
| **Amazon CloudFront** | Global CDN; HTTPS-only; serves private S3 frontend; HTTP/2 + HTTP/3 + IPv6 |
| **Amazon S3** | Private frontend hosting; Public Access Block; AES-256 SSE |
| **Amazon Bedrock (Nova Lite)** | Generative AI contextual analysis & explanation |
| **AWS SAM (Serverless Application Model)** | Infrastructure-as-Code for Lambda, API, DynamoDB, CloudFront, S3 |
| **AWS CloudFormation** | Underlying IaC stack provisioning |
| **Amazon CloudWatch** | Structured JSON logging with 14-day retention |

### 🐍 Backend (Python 3.12)

| Library / Tool | Role |
|---|---|
| **boto3 / botocore** | AWS SDK — DynamoDB, Bedrock Converse API |
| **Python `re`** | Regex-based rule engine and URL extraction |
| **Python `math`, `collections`** | TF-IDF IDF computation and Shannon entropy calculation |
| **Python `urllib.parse`** | Offline passive URL structural analysis |
| **Python `ipaddress`** | IP-host detection in URLs |
| **Python `json`, `uuid`, `datetime`** | Serialization, ID generation, timestamps |
| **Ruff** | Python linter and code quality enforcer |
| **pytest** | Unit, edge, integration, privacy, and URL intelligence tests |

> **Zero heavy ML dependencies in Lambda.** TF-IDF vectorization and logistic regression are implemented from scratch using only the Python standard library — keeping the Lambda deployment package tiny and cold starts fast.

### 🌐 Frontend

| Technology | Role |
|---|---|
| **Vanilla JavaScript (ES2020+)** | SPA logic — scan, history, dashboard, localization |
| **HTML5** | Semantic single-page markup |
| **CSS3 (Custom Properties)** | Dark-mode mobile-first responsive design with CSS Grid and Flexbox |
| **Inter Font** | UI typography via system font stack fallback |
| **Fetch API** | Async communication with the backend API |

> No frontend framework (React, Vue, Angular) or build tool (Webpack, Vite) is required. The frontend is pure static files that can be served from any CDN.

### 🔁 CI/CD

| Tool | Role |
|---|---|
| **GitHub Actions** | Full automated CI pipeline on push and pull request |
| **AWS SAM CLI** | `sam validate --lint` + `sam build` in CI |
| **Node.js (`--check`)** | Frontend JavaScript syntax validation |
| **`git diff --exit-code`** | Reproducibility guard — rejects committed ML artifact drift |
| **`git grep`** | Committed-secret pattern detection (AWS keys, private keys) |

---

## 🔍 Detection Layers

RuralShield uses a **four-layer hybrid detector**. Scores from all available layers are combined by a weighted aggregation engine that automatically renormalizes weights if a layer is unavailable.

### Layer 1 — ML Predictor (`ml_predictor.py`)
- **Algorithm:** TF-IDF + Logistic Regression (implemented from scratch in pure Python)
- **Vectorization:** Normalized TF-IDF with sub-linear TF scaling
- **Training:** Stratified train/validation/test split; deterministic seeded shuffle; L2 regularization; decaying learning rate over 80 epochs
- **Artifact:** Serialized as `model.json` (vocabulary + IDF array + weight vector + intercept); loaded directly in Lambda with no dependencies
- **Default weight:** 40%

### Layer 2 — Rule Engine (`rules.py`)
- 13 explainable social-engineering rules with `rule_id`, `severity`, and `contribution` points:

| Rule ID | Trigger | Severity |
|---|---|---|
| `OTP_REQUEST` | Requests an OTP | High |
| `PIN_REQUEST` | Requests a PIN or MPIN | High |
| `PASSWORD_REQUEST` | Requests a password | High |
| `CREDENTIAL_REQUEST` | Requests card/account/CVV details | High |
| `ACCOUNT_THREAT` | Threatens account suspension/block/freeze | High |
| `FAKE_KYC` | KYC verification pressure | High |
| `URGENT_LANGUAGE` | "Urgent", "act now", "within N hours" | Medium |
| `PAYMENT_DEMAND` | Demands a UPI/INR payment | Medium |
| `LOTTERY_REWARD` | Promises unexpected reward/lottery | Medium |
| `FAKE_REFUND` | Uses refund or cashback lure | Medium |
| `LOAN_SCAM` | Unsolicited pre-approved loan offer | Medium |
| `FAKE_SUPPORT` | Claims to be bank customer care | Medium |
| `IMPERSONATION` | Uses SBI, HDFC, RBI, ICICI brand names | Low |

- **Default weight:** 20%

### Layer 3 — Passive URL Analyzer (`url_analyzer.py`)
Fully offline — **never fetches the submitted URL**:

| Signal | Points |
|---|---|
| Non-HTTPS scheme | +8 |
| URL length > 90 characters | +10 |
| Hostname length > 45 characters | +8 |
| 3+ subdomain levels | +3 per level (max +14) |
| `@` symbol in URL | +18 |
| URL-encoded characters | +8 |
| IP address host | +22 |
| Known URL shortener (bit.ly, t.co, tinyurl, etc.) | +15 |
| IDN / punycode internationalized characters | +18 |
| Suspicious banking keywords in URL | +4 per keyword (max +18) |
| Bank brand in non-brand domain | +20 |
| One-edit Levenshtein typo of a bank brand | +22 |
| Domain pattern matches bank impersonation regex | +15 |
| High-entropy domain (DGA-like) | +10 |

- Supports up to **5 unique URLs per message**; the highest-risk URL score contributes to fusion
- **Default weight:** 25%

### Layer 4 — Amazon Bedrock Context (`bedrock_service.py`)
- **Model:** `amazon.nova-lite-v1:0` (configurable)
- **Protocol:** Bedrock Converse API with structured JSON output validation
- **Prompt engineering:** System prompt strictly frames submitted content as untrusted data, never as instructions (prompt injection resistance)
- **Output schema:** `summary`, `reasons`, `recommended_action`, `scam_category`, `ai_risk_score` (0–100)
- **Scam categories:** Bank Impersonation, KYC Scam, OTP Scam, UPI Scam, Loan Scam, Lottery/Reward Scam, Fake Customer Support, Payment Scam, Other/Unknown
- **Timeouts:** 2s connect / 8s read; max 2 retries; failure-safe fallback to rules/URL reasons
- **Default weight:** 15%

### Risk Fusion (`risk_engine.py`)

```
Risk Score = Σ (component_score × component_weight) / Σ (active_weights)

Classification:
  0–30   → SAFE
  31–65  → SUSPICIOUS
  66–100 → PHISHING
```

Weights are configurable via Lambda environment variables (`ML_WEIGHT`, `URL_WEIGHT`, `RULE_WEIGHT`, `AI_WEIGHT`) and renormalize automatically if a component is unavailable.

---

## 📊 ML Model & Evaluation

### Training Pipeline (`ml/train.py`)

- Deterministic, dependency-light training in pure Python
- Stratified 70/15/15 train/validation/test split with fixed seed (42)
- TF-IDF vocabulary (up to 6,000 features) with `doc_freq >= 2` threshold
- Logistic regression: 80 epochs, L2=0.0005, decaying learning rate

### Component Ablation (40-row synthetic demo corpus)

| Variant | Accuracy | Phishing Precision | Phishing Recall | Phishing F1 |
|---|---:|---:|---:|---:|
| Rules only | 0.525 | 0.6667 | 0.10 | 0.1739 |
| **ML only** | **0.925** | **1.0** | **0.85** | **0.9189** |
| ML + Rules | 0.875 | 1.0 | 0.75 | 0.8571 |
| ML + Rules + URL | 0.775 | 1.0 | 0.55 | 0.7097 |

> ⚠️ **Important:** Metrics are from a 40-row **synthetic demo dataset**. They are not production benchmarks. Held-out validation/test splits of 6 examples carry very high uncertainty. The hybrid is not yet claimed superior to ML-only — threshold and weight selection requires a larger licensed corpus.

### What "CI Reproducibility" Means

Every CI run retrains the model from scratch and runs `git diff --exit-code` on the serialized artifacts. If anyone modifies the training data or pipeline and doesn't recommit the updated artifact, CI fails.

---

## 📡 API Reference

### `POST /scan`
Analyze a suspicious message or URL.

**Request:**
```json
{
  "type": "message",
  "text": "URGENT: Your KYC expires today. Verify at http://sbi-kyc.example to avoid block.",
  "language": "en"
}
```

**Response:**
```json
{
  "scan_id": "uuid",
  "timestamp": "2026-08-28T14:30:00Z",
  "classification": "PHISHING",
  "risk_score": 82.5,
  "confidence": 0.91,
  "detected_language": "en",
  "scam_category": "KYC Scam",
  "reasons": ["Uses KYC verification pressure", "Contains a URL that should be checked", "..."],
  "recommendation": "Do not click the link. Contact your bank through its official app or toll-free number.",
  "summary": "This message uses urgency and KYC pressure — a common bank phishing tactic.",
  "components": { "ml": 88.1, "rules": 34, "url": 72, "ai": 85 },
  "weights_used": { "ml": 0.40, "rules": 0.20, "url": 0.25, "ai": 0.15 }
}
```

### `GET /history`
Owner-scoped scan history (requires authenticated identity). Returns up to 50 records.

### `GET /statistics`
Owner-scoped aggregated stats: total scans, classification breakdown, scam category distribution.

### `GET /health`
Returns `{"status": "ok", "service": "RuralShield AI"}`.

> The client sends `X-RuralShield-Client-ID` (random browser UUID). API Gateway JWT `sub` claims take precedence when present — enabling a future Cognito/OIDC drop-in without changing the storage model. See [`docs/api.md`](docs/api.md).

---

## 🔒 Privacy Model

| Principle | Implementation |
|---|---|
| **No raw message persistence** | `save_scan()` stores only derived metadata — classification, score, language, rule IDs, URL domain, scam category |
| **No fingerprinting** | Message fingerprinting was intentionally removed — a deterministic hash of predictable SMS text can be dictionary-tested |
| **Redaction before AI** | `sanitizer.py` redacts OTP/PIN/card-like patterns before Bedrock processing |
| **Prompt injection resistance** | System prompt explicitly marks submitted text as untrusted data, not instructions |
| **Device-local identity** | Each browser generates a random `client#<uuid>` — not tied to a real identity |
| **No anonymous history** | Scans without a valid identity are not persisted; history/statistics endpoints return 401 for anonymous callers |
| **JWT-ready** | Storage model supports future `user#<jwt-sub>` migration without schema changes |

**DynamoDB key design:**
```
PK  owner_id  = client#<random-id>   or   user#<jwt-sub>
SK  scan_key  = <ISO-timestamp>#<scan-uuid>
```

History uses `Query` with the owner partition key — never a full table `Scan`.

---

## 🛡️ Security Controls

| Control | Detail |
|---|---|
| **Input validation** | Strict JSON schema, field type checks, 5,000-character message limit |
| **No SSRF** | URL analyzer parses structure offline; no server-side URL fetching |
| **Private S3 + OAC** | Frontend bucket has full Public Access Block; CloudFront uses SigV4-signed OAC |
| **HTTPS-only** | CloudFront enforces redirect-to-HTTPS |
| **CORS** | Exact-origin CORS configured at deployment time; wildcard `*` is never used in production |
| **API throttling** | 10 RPS rate limit, 20-request burst limit via API Gateway |
| **Least-privilege IAM** | Lambda policy grants only `dynamodb:PutItem` + `dynamodb:Query` on the specific table ARN, and `bedrock:InvokeModel` on the specific model ARN |
| **DynamoDB encryption** | Server-side encryption (SSE) enabled; Point-In-Time Recovery (PITR) enabled |
| **Bedrock safety** | Bounded retries, strict timeouts, structured output validation, fallback on all failure modes |
| **No sensitive logging** | CloudWatch logs contain only `request_id`, `duration_ms`, `classification`, `risk_score`, and error class — never raw message content or secrets |
| **Defensive HTTP headers** | `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, CSP `default-src 'none'` |
| **Secret leak guard** | GitHub Actions CI scans for AWS key patterns and private key headers on every push |
| **Log retention** | CloudWatch log group retention set to 14 days |

See [`docs/security.md`](docs/security.md) for the full threat model and residual risks.

---

## 🌐 Multilingual Support

The UI and scan results support **English**, **Hindi (हिन्दी)**, and **Tamil (தமிழ்)** via a lightweight i18n locale map in the frontend.

> ⚠️ **Important distinction:** Translated UI is not evidence of multilingual ML quality. The current TF-IDF model is trained on an English-primary synthetic corpus. Hinglish/Tanglish (code-switched) and per-language ML evaluation require a substantially larger licensed corpus. This distinction is intentional and documented.

---

## 📁 Repository Layout

```
ruralshield/
├── backend/
│   ├── lambda/
│   │   ├── handler.py          # HTTP routing & orchestration
│   │   ├── validators.py       # Input validation & schema checks
│   │   ├── sanitizer.py        # PII/secret redaction
│   │   ├── language.py         # Language detection & normalization
│   │   ├── ml_predictor.py     # TF-IDF + LogReg inference
│   │   ├── model.json          # Serialized trained model artifact
│   │   ├── rules.py            # 13 explainable social-engineering rules
│   │   ├── url_analyzer.py     # Passive offline URL heuristics
│   │   ├── bedrock_service.py  # Amazon Bedrock Converse API integration
│   │   ├── risk_engine.py      # Weighted score fusion & classification
│   │   ├── storage.py          # DynamoDB persistence (history + statistics)
│   │   └── config.py           # Environment-variable-driven configuration
│   └── requirements.txt        # boto3, botocore (Lambda runtime dependencies)
│
├── frontend/
│   ├── index.html              # Semantic HTML5 SPA shell
│   ├── app.js                  # Vanilla JS — scan, history, dashboard, i18n
│   ├── styles.css              # Dark-mode CSS3 — Grid, Flexbox, custom properties
│   └── runtime-config.js       # Injected at deploy time: API endpoint
│
├── infrastructure/
│   └── template.yaml           # AWS SAM / CloudFormation IaC template
│
├── ml/
│   ├── train.py                # Deterministic training pipeline (pure Python)
│   ├── evaluate_hybrid.py      # Component ablation evaluation
│   ├── evaluation.json         # ML evaluation output (committed artifact)
│   ├── hybrid_evaluation.json  # Ablation results (committed artifact)
│   └── data/
│       └── demo_dataset.csv    # 40-row synthetic demo corpus (not a benchmark)
│
├── scripts/
│   ├── deploy.sh               # End-to-end SAM + CloudFront deploy (Linux/macOS)
│   ├── deploy.ps1              # End-to-end SAM + CloudFront deploy (Windows)
│   ├── setup.sh                # Local dev environment setup (Linux/macOS)
│   └── setup.ps1               # Local dev environment setup (Windows)
│
├── tests/
│   ├── test_core.py            # Core detection logic unit tests
│   ├── test_edge_cases.py      # Edge cases and boundary tests
│   ├── test_integrations.py    # End-to-end integration tests
│   ├── test_privacy_boundaries.py  # Privacy guarantee tests
│   ├── test_risk_availability.py   # Component unavailability/degradation tests
│   └── test_url_intelligence.py    # URL analyzer heuristic tests
│
├── docs/
│   ├── api.md                  # Full API contract and examples
│   ├── architecture.md         # Architecture deep-dive and failure modes
│   └── security.md             # Threat model, controls, and residual risks
│
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI pipeline
│
├── .gitignore
└── README.md
```

---

## 💻 Local Development

### Prerequisites

- Python 3.12+
- Node.js (for frontend JS syntax check)

### Setup

```bash
# Clone and create virtual environment
python -m venv .venv

# Activate
# Windows:   .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt pytest ruff

# Or use the setup script:
# Linux/macOS: bash scripts/setup.sh
# Windows:     .\scripts\setup.ps1
```

### Run the ML Pipeline

```bash
# Train model and serialize artifact
python ml/train.py

# Run component ablation evaluation
python ml/evaluate_hybrid.py
```

### Run Tests

```bash
pytest -q
```

### Run Lint

```bash
ruff check backend/lambda ml tests
```

### Serve Frontend Locally

```bash
python -m http.server 8080 -d frontend
# Open http://localhost:8080
```

> When running locally without a deployed backend, set `window.RURALSHIELD_API_URL` in browser DevTools console, or use the Settings panel in the UI.

---

## 🚀 AWS Deployment

### Prerequisites

- AWS CLI configured with appropriate permissions
- AWS SAM CLI installed
- Amazon Bedrock model access enabled in the target region (`amazon.nova-lite-v1:0` in `ap-south-1` by default)

### Deploy

```bash
# Linux/macOS
./scripts/deploy.sh ruralshield-ai

# Windows PowerShell
.\scripts\deploy.ps1 -StackName ruralshield-ai
```

The deploy script performs:
1. `sam build` — packages Lambda function and dependencies
2. `sam deploy` — provisions CloudFormation stack (Lambda, API Gateway, DynamoDB, S3, CloudFront)
3. Retrieves the generated CloudFront origin URL
4. Redeploys to update API CORS to the exact CloudFront origin
5. Injects the API endpoint into a temporary frontend copy
6. `aws s3 sync` — uploads frontend to the private S3 bucket
7. `aws cloudfront create-invalidation` — clears the CDN cache

> **Note:** `sam validate --lint` passing in CI is not a substitute for a live smoke test. A real AWS deployment has not been verified until the full deploy script is run in an authorized account.

### Configuration Parameters

| SAM Parameter | Default | Description |
|---|---|---|
| `AllowedOrigin` | `http://localhost:8080` | Frontend origin for CORS (set automatically by deploy script) |
| `BedrockModelId` | `amazon.nova-lite-v1:0` | Bedrock foundation model ID |

### Environment Variables (Lambda)

| Variable | Default | Description |
|---|---|---|
| `ML_WEIGHT` | `0.40` | ML layer fusion weight |
| `URL_WEIGHT` | `0.25` | URL analyzer fusion weight |
| `RULE_WEIGHT` | `0.20` | Rule engine fusion weight |
| `AI_WEIGHT` | `0.15` | Bedrock AI fusion weight |
| `SAFE_MAX` | `30` | Risk score threshold for SAFE |
| `SUSPICIOUS_MAX` | `65` | Risk score threshold for SUSPICIOUS |
| `MAX_TEXT_LENGTH` | `5000` | Maximum allowed input characters |
| `BEDROCK_MODEL_ID` | _(injected)_ | Active Bedrock model ARN |
| `TABLE_NAME` | _(injected)_ | DynamoDB table name |
| `AWS_REGION` | `ap-south-1` | AWS region |

---

## ✅ CI / Quality Gate

Every push and pull request triggers the full GitHub Actions CI pipeline:

| Step | Tool | Purpose |
|---|---|---|
| Secrets scan | `git grep` | Detect committed AWS keys / private keys |
| Lint | `ruff` | Enforce Python code quality |
| ML retrain | `python ml/train.py` | Reproduce model from source data |
| Artifact drift check | `git diff --exit-code` | Fail if model.json or eval JSONs changed |
| Ablation eval | `python ml/evaluate_hybrid.py` | Reproduce evaluation results |
| Unit & integration tests | `pytest` | 6 test modules: core, edge, integration, privacy, availability, URL |
| Python bytecode compile | `python -m compileall` | Catch syntax/import errors in all modules |
| Frontend asset check | `test -s` + `node --check` | Verify HTML/CSS/JS exist and JS is valid syntax |
| IaC validation | `sam validate --lint` | Lint the CloudFormation/SAM template |
| SAM build | `sam build` | Full package build as done in real deployment |
| Lambda package check | `test -s` | Verify handler, model, and risk engine are in the built package |

---

## 🌍 SDG Alignment

| Goal | Connection |
|---|---|
| **SDG 9 — Industry, Innovation and Infrastructure** | Applying AI/ML and cloud infrastructure to an under-served domain (rural financial security) |
| **SDG 10 — Reduced Inequalities** | Protecting economically vulnerable rural banking users who may have lower digital literacy |
| **SDG 1 — No Poverty** | Reducing fraud-related financial losses that disproportionately affect low-income households |

---

## 🔮 What "Production-Grade" Still Requires

This repository intentionally documents remaining gaps with measurable acceptance criteria:

1. **Real Dataset:** A license-compatible, deduplicated corpus large enough for English/Hindi/Tamil/Hinglish/Tanglish evaluation with documented source provenance and leakage controls. The bundled 40-row synthetic dataset is for pipeline reproducibility only.

2. **Rigorous Evaluation:** Frozen train/validation/test partitions; per-language and code-switched metrics; confidence intervals; calibration curves; threshold and weight selection only on the validation set; final reporting only on the untouched test set.

3. **External URL Intelligence:** Optional reputation/domain-age feed integration (e.g., Google Safe Browsing, WHOIS) with strict timeouts and privacy controls. Structural analysis must continue working offline.

4. **Authentication:** Cognito/OIDC JWT authorizer if multi-device user accounts are required. The current random browser identity is intentionally device-local, not authentication.

5. **Live AWS Verification:** End-to-end deploy, smoke test (API, CloudFront, Bedrock, DynamoDB), latency/cold start measurement, and rollback testing in an authorized account.

6. **Abuse & Operations:** AWS WAF at the CloudFront edge, CloudWatch alarms/SLOs, cost budgets, SAST/dependency scanning, and incident runbooks.

7. **UX Field Validation:** Usability and accessibility testing with the intended rural audience; evidence-driven decisions on share-to-scan, PWA offline mode, and text-to-speech read-aloud features.

> These gaps cannot be honestly resolved by inventing synthetic code or accuracy. They require licensed data, a real AWS account, and real user research.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for rural banking security** · AWS Course Project

</div>
