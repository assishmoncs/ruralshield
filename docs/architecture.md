# Architecture

RuralShield uses a hybrid detector because no single signal is reliable enough for phishing decisions.

```text
Static mobile UI (S3)
        |
API Gateway HTTP API
        |
Lambda orchestration
  |       |       |       |
  ML    Rules    URL    Bedrock
  |       |       |       |
  +-------+-------+-------+
              |
         Risk engine
          /       \
     response   DynamoDB
                   |
               CloudWatch logs
```

## Backend modules
- `validators.py`: API/input contract and size checks.
- `sanitizer.py`: redaction and safe fingerprints.
- `language.py`: lightweight language detection/normalization support.
- `ml_predictor.py`: serialized model inference with a documented fallback when an artifact is unavailable.
- `rules.py`: explainable social-engineering signals with IDs/severity/contribution.
- `url_analyzer.py`: passive structural URL features; never fetches submitted URLs.
- `bedrock_service.py`: constrained contextual explanation with defensive parsing/fallback.
- `risk_engine.py`: configurable weighted aggregation and thresholds.
- `storage.py`: DynamoDB persistence/history/statistics without raw sensitive content.
- `handler.py`: HTTP routing and orchestration, kept separate from core detectors.

## Failure modes
Bedrock failure does not prevent a result. DynamoDB failure should not turn a completed detection into an unsafe classification; persistence failure is logged separately. Missing model artifacts degrade the ML signal rather than silently inventing a trained probability. Malformed requests return 4xx errors. Unexpected service failures return sanitized 5xx responses.

## Performance
The design uses one small serverless function package, static frontend assets, lazy AWS SDK client reuse and a lightweight linear text model. This keeps deployment understandable while avoiding an unnecessary service graph.