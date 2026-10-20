# Architecture

RuralShield uses a hybrid detector because no single signal is reliable enough for phishing-risk assessment.

## Request and decision flow

    Browser / mobile UI
       |-- HTTPS static assets --> CloudFront --> Private S3 (OAC)
       |
       |-- HTTPS API calls --> API Gateway HTTP API --> Lambda orchestrator
                                                        |
                                  +---------------------+------------------+
                                  |                     |                  |
                                  v                     v                  v
                           TF-IDF + LR           Contextual rules    Passive URL
                           ML classifier           and mitigations    heuristics
                                  |                     |                  |
                                  +---------------------+------------------+
                                                        |
                                                        v
                                          Deterministic risk engine
                                          (ML + rules + URL only)
                                                        |
                                                        v
                                                Risk verdict + score
                                                        |
                                                        +-------------------+
                                                                            |
    Lambda orchestrator --> Amazon Bedrock (optional) ---------------------+
                           explanation and recommended action only
                                                                            |
                                                                            v
                                                             Combined API response

    Authenticated API requests -- Cognito JWT --> API Gateway authorizer
    Lambda -- derived authenticated scan metadata --> DynamoDB
    Lambda -- operational metadata logs ----------> CloudWatch

Bedrock is an optional explanation layer. It is not an input to the final security score. If Bedrock is unavailable, the local detection pipeline can still return a verdict and a fallback recommendation.

## Backend modules

- validators.py: validates scan/feedback input shape, type, size, and IDs.
- sanitizer.py: redacts common secret patterns before downstream AI processing.
- language.py: lightweight language detection and normalization support.
- ml_predictor.py: inference using the serialized TF-IDF/logistic-regression model.
- rules.py: explainable social-engineering signals with rule IDs and contributions.
- url_analyzer.py: passive URL parsing and structural risk indicators without fetching URLs.
- bedrock_service.py: optional contextual explanation, defensive response parsing, and fallback handling.
- risk_engine.py: deterministic aggregation, thresholds, classification, and qualitative decision-strength label.
- storage.py: owner-scoped derived scan records, history, statistics, and feedback.
- handler.py: HTTP routing, orchestration, response generation, and operational logging.

## Persistence and failure behavior

Only authenticated scans are eligible for personal history persistence. Raw message bodies are not saved in scan records. A persistence failure does not change the calculated verdict; the API reports persistence status separately. Bedrock failures use fallback text rather than blocking the core verdict. Malformed scan requests return client errors. The analyzer never connects to the supplied URL.

## Deployment

The infrastructure is defined in infrastructure/template.yaml using AWS SAM/CloudFormation. The template provisions a private S3 bucket, CloudFront distribution with Origin Access Control, an API Gateway HTTP API, Lambda, DynamoDB, Cognito, and the associated IAM/logging configuration. CI validates the SAM template and builds the Lambda package. This is not a substitute for a live deployment smoke test.
