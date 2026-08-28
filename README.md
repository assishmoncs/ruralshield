<div align="center">

<h1>🛡️ RuralShield AI</h1>

<p><strong>Privacy-first, explainable phishing-risk detection for rural banking users.</strong></p>

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12"/>
  <img src="https://img.shields.io/badge/AWS_Lambda-Serverless-FF9900?style=for-the-badge&logo=awslambda&logoColor=white" alt="AWS Lambda"/>
  <img src="https://img.shields.io/badge/Amazon_Bedrock-Generative_AI-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white" alt="Amazon Bedrock"/>
  <img src="https://img.shields.io/badge/DynamoDB-NoSQL-4053D6?style=for-the-badge&logo=amazondynamodb&logoColor=white" alt="Amazon DynamoDB"/>
  <img src="https://img.shields.io/badge/CloudFront-CDN-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white" alt="CloudFront"/>
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="MIT License"/>
  <img src="https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" alt="GitHub Actions CI"/>
</p>

<p>
  <img src="https://img.shields.io/badge/SDG_9-Industry_%26_Innovation-FD6925?style=flat-square" alt="SDG 9"/>
  <img src="https://img.shields.io/badge/SDG_10-Reduced_Inequalities-DD1367?style=flat-square" alt="SDG 10"/>
</p>

</div>

---

RuralShield AI is a serverless, mobile-first phishing-risk detection system for rural banking users. It combines a lightweight trained ML model, deterministic social-engineering rules, passive URL heuristics, and optional Amazon Bedrock contextual analysis into a single explainable workflow while minimizing persistent sensitive data.

> ⚠️ **Safety Notice:** Never enter a real OTP, PIN, password, or complete card number into RuralShield AI. This is a research and educational prototype, not a certified bank fraud engine. Detection is probabilistic.

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
- [What Production Deployment Still Requires](#-what-production-deployment-still-requires)

## 🎯 What It Does

`POST /scan` accepts a suspicious banking message or URL and returns:

| Field | Description |
|---|---|
| `classification` | `SAFE`, `SUSPICIOUS`, or `PHISHING` |
| `risk_score` | Deterministic 0–100 risk score from the security detection path |
| `confidence_level` | Qualitative decision strength (`LOW`, `MEDIUM`, `HIGH`), **not** a calibrated probability |
| `reasons` | Human-readable detection signals |
| `detected_language` | `en`, `hi`, or `ta` |
| `scam_category` | Categorized scam type |
| `recommendation` | Plain-language safety guidance |
| `components` | ML, URL, rules, and AI observability values |
| `model_version` | Version of the ML artifact used for the scan |

**Important:** Amazon Bedrock is **not** part of the final security decision. The security decision uses ML + rules + passive URL evidence. Bedrock is a contextual explanation layer and can be disabled/fail without preventing a local security verdict.

## 🏛️ Architecture

```text
Browser / Mobile UI
        │ HTTPS
        ▼
   CloudFront ─────────────► Private S3
        │
        ▼
   API Gateway HTTP API
        │
        ▼
      Lambda
        │
   ┌────┼───────────────┐
   ▼    ▼       ▼       ▼
  ML   Rules    URL   Bedrock
   │    │       │    (context only)
   └────┴───────┘
          │
          ▼
   Deterministic Risk Engine
          │
          ├──────────────► API result
          │
          ▼
      DynamoDB
          │
          ▼
     CloudWatch

Cognito JWT ──► authenticated history / statistics / feedback
IAM ──────────► least-privilege AWS access
```

The frontend bucket is private and delivered through CloudFront using Origin Access Control (OAC). The API never fetches submitted URLs; URL analysis is passive and local.

## 🛠️ Tech Stack

### AWS

| Service | Role |
|---|---|
| AWS Lambda | Serverless Python backend |
| API Gateway HTTP API | API routing, CORS, throttling |
| DynamoDB | Owner-scoped sanitized scan metadata |
| Amazon Bedrock | Optional contextual explanation using Nova Lite |
| Amazon S3 | Private static frontend storage |
| Amazon CloudFront | HTTPS frontend delivery and CDN |
| Amazon Cognito | Authentication for private user data |
| AWS IAM | Least-privilege service authorization |
| Amazon CloudWatch | Logs and operational visibility |
| AWS SAM / CloudFormation | Infrastructure as Code |

### Backend

- Python 3.12
- Pure-Python TF-IDF + logistic regression inference
- `boto3` / `botocore`
- `pytest`
- `ruff`

### Frontend

- HTML5
- CSS3
- Vanilla JavaScript (ES2020+)
- Fetch API
- Lightweight localization for English, Hindi, and Tamil

## 🔍 Detection Layers

### 1. Machine Learning

The current lightweight detector is **TF-IDF + Logistic Regression**, implemented without heavyweight ML dependencies in Lambda. The repository contains the deterministic training pipeline, serialized model artifact, model version metadata, and evaluation output.

### 2. Rule Engine

Explainable social-engineering rules identify signals such as:

- OTP/PIN/password requests
- credential requests
- account threats
- KYC pressure
- urgency
- payment demands
- lottery/reward lures
- fake refunds
- loan scams
- fake support
- bank impersonation

Rules also include mitigating security-awareness signals to reduce obvious false positives such as messages saying that a bank will never ask for an OTP.

### 3. Passive URL Analyzer

The analyzer never visits submitted URLs. It inspects structural indicators such as:

- IP-address hosts
- `@` URL confusion
- URL/hostname length
- suspicious subdomain depth
- URL shorteners
- encoded characters
- IDN/punycode
- bank-brand impersonation
- typo-like domains
- suspicious keywords
- high-entropy domains

These are risk signals, not proof of maliciousness.

### 4. Amazon Bedrock

Bedrock uses the sanitized message and structured local evidence to generate:

- plain-language summary
- explanation reasons
- scam category
- recommended action

Prompt instructions explicitly treat submitted content as untrusted data. Model output is validated defensively. Bedrock does not override the deterministic security decision.

## 🧮 Risk Decision

The security score uses the active deterministic components:

```text
Risk Score = weighted average of active ML + URL + Rules scores
```

Default weights:

```text
ML       40%
URL      25%
Rules    20%
```

The remaining 15% is intentionally **not used by the security decision** because Bedrock is explanation/context only. If ML or URL analysis is unavailable, the active weights are automatically renormalized.

Classification thresholds are configurable:

```text
0–30    SAFE
31–65   SUSPICIOUS
66–100  PHISHING
```

`confidence_level` is a qualitative strength indicator and must not be interpreted as a calibrated probability.

## 📊 ML Model & Evaluation

The repository currently uses a **40-row synthetic demo dataset** solely for deterministic development and CI reproducibility:

- 20 safe examples
- 20 phishing examples
- 28 training rows
- 6 validation rows
- 6 test rows
- fixed seed: 42

Current held-out evaluation is:

| Metric | Validation | Test |
|---|---:|---:|
| Accuracy | 83.33% | 83.33% |
| Phishing precision | 100% | 100% |
| Phishing recall | 66.67% | 66.67% |
| Phishing F1 | 80.00% | 80.00% |

These numbers are **not production benchmarks**. The test partition contains only six examples. They should be replaced by evaluation on a larger, license-compatible, deduplicated real-world corpus before making meaningful performance claims.

The repository intentionally keeps the synthetic corpus so CI can reproduce the exact model artifact.

## 📡 API Reference

### `POST /scan`

Public scan endpoint. Anonymous scans are allowed, but are not persisted as personal history unless an authenticated Cognito ID token is present.

Example request:

```json
{
  "type": "message",
  "text": "URGENT: Your KYC expires today. Verify at http://example.invalid to avoid account block.",
  "language": "en"
}
```

The response contains the classification, risk score, qualitative confidence level, reasons, language, scam category, model version, component scores, URL analysis, and whether Bedrock was available.

### `GET /history`

Authenticated endpoint. Returns only records belonging to the authenticated Cognito user.

### `GET /statistics`

Authenticated endpoint. Returns statistics computed from that user's stored scan records.

### `POST /feedback`

Authenticated endpoint. Records whether a stored result was helpful or incorrect after verifying ownership.

### `GET /health`

Public liveness endpoint.

## 🔒 Privacy Model

RuralShield minimizes persistence of sensitive content:

- raw message bodies are not stored
- only derived scan metadata is persisted
- obvious OTP/card/password/account patterns are redacted before downstream AI/persistence where practical
- anonymous scans are not persisted as user history
- authenticated records are owner-scoped by Cognito user ID
- CloudWatch logging excludes raw message content and secrets

Never enter real banking credentials into the application.

## 🛡️ Security Controls

Implemented controls include:

- strict request validation and bounded input size
- private S3 bucket with Public Access Block
- CloudFront Origin Access Control
- HTTPS-only CloudFront delivery
- exact-origin CORS configuration
- API throttling
- least-privilege Lambda IAM policies
- DynamoDB server-side encryption and PITR
- passive URL analysis with no server-side URL fetching
- prompt-injection-aware Bedrock system instructions
- defensive Bedrock response validation and failure fallback
- Cognito JWT authentication for private endpoints
- server-side ownership enforcement
- defensive HTTP headers
- secret-leak checks in GitHub Actions
- CloudWatch log retention

See [`docs/security.md`](docs/security.md) for the threat model and residual risks.

## 🌐 Multilingual Support

The interface supports:

- English
- Hindi (हिन्दी)
- Tamil (தமிழ்)

This is primarily a UI/localization feature at the current stage. The bundled ML corpus is English-primary and is not sufficient to claim production-quality multilingual phishing detection.

## 📁 Repository Layout

```text
ruralshield/
├── backend/
│   └── lambda/
│       ├── handler.py
│       ├── validators.py
│       ├── sanitizer.py
│       ├── language.py
│       ├── ml_predictor.py
│       ├── model.json
│       ├── rules.py
│       ├── url_analyzer.py
│       ├── bedrock_service.py
│       ├── risk_engine.py
│       ├── storage.py
│       └── config.py
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── auth.js
│   ├── styles.css
│   └── runtime-config.js
│
├── infrastructure/
│   └── template.yaml
│
├── ml/
│   ├── train.py
│   ├── evaluate_hybrid.py
│   ├── evaluation.json
│   ├── hybrid_evaluation.json
│   └── data/
│       └── demo_dataset.csv
│
├── tests/
│   ├── test_core.py
│   ├── test_edge_cases.py
│   ├── test_integrations.py
│   ├── test_privacy_boundaries.py
│   ├── test_risk_availability.py
│   └── test_url_intelligence.py
│
├── scripts/
│   ├── deploy.sh
│   ├── deploy.ps1
│   ├── setup.sh
│   └── setup.ps1
│
├── docs/
│   ├── api.md
│   ├── architecture.md
│   ├── architecture-decisions.md
│   ├── model-card.md
│   └── security.md
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .gitignore
└── README.md
```

## 💻 Local Development

### Prerequisites

- Python 3.12+
- Node.js
- AWS SAM CLI for infrastructure validation/build

### Setup

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# Linux/macOS
source .venv/bin/activate

pip install -r backend/requirements.txt pytest ruff
```

### Train / evaluate

```bash
python ml/train.py
python ml/evaluate_hybrid.py
```

### Test

```bash
pytest -q
```

### Lint

```bash
ruff check backend/lambda ml tests
```

### Local frontend

```bash
python -m http.server 8080 -d frontend
```

## 🚀 AWS Deployment

### Requirements

- AWS CLI authenticated with appropriate permissions
- AWS SAM CLI
- Amazon Bedrock access to the configured model in the target region

Default region:

```text
ap-south-1
```

Default Bedrock model:

```text
amazon.nova-lite-v1:0
```

### Deploy on Windows

```powershell
.\\scripts\\deploy.ps1 -StackName ruralshield-ai
```

### Deploy on Linux/macOS

```bash
./scripts/deploy.sh ruralshield-ai
```

The deployment scripts build the SAM application, provision AWS resources, configure the exact frontend origin for CORS, inject runtime API/Cognito configuration, upload the static frontend to the private S3 bucket, and invalidate CloudFront.

> CI validation is not a live AWS smoke test. A deployment should only be called verified after running it in an authorized AWS account and testing `/health`, `/scan`, authentication, history, statistics, and feedback.

## ✅ CI / Quality Gate

GitHub Actions verifies:

- committed-secret patterns
- Ruff linting
- ML training/artifact reproducibility
- hybrid evaluation reproducibility
- pytest regression suite
- Python compilation
- frontend asset and JavaScript syntax checks
- SAM template validation
- SAM build
- Lambda package contents

The current test suite includes **60+ automated tests** across core detection, edge cases, integrations, privacy boundaries, component degradation, and URL intelligence.

## 🌍 SDG Alignment

| Goal | Connection |
|---|---|
| **SDG 9 — Industry, Innovation and Infrastructure** | Uses AI/ML, serverless cloud infrastructure, and secure digital services to improve phishing-risk protection for rural banking. |
| **SDG 10 — Reduced Inequalities** | Focuses on improving digital-safety access for rural and underserved banking users who may face greater digital-literacy barriers. |

## 🔮 What Production Deployment Still Requires

The project is intentionally honest about the remaining gaps:

1. A larger, license-compatible, deduplicated real-world phishing corpus.
2. Frozen train/validation/test partitions with leakage controls and stronger statistical evaluation.
3. Probability calibration if numeric confidence is presented.
4. Per-language and code-switched evaluation for Hindi/Tamil/Hinglish/Tanglish.
5. Optional reputation-based URL intelligence with strict privacy/timeouts.
6. Live AWS smoke testing, latency measurement, rollback testing, and cost monitoring.
7. WAF/advanced abuse protection, CloudWatch alarms, SLOs, and operational runbooks for a public deployment.
8. Broader usability/accessibility validation with the intended rural audience.

These requirements cannot be honestly substituted with fabricated metrics or synthetic evidence.

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

<div align="center">

**Built for rural banking security with AWS, AI/ML, and privacy by design.**

</div>
