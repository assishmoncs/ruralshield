# RuralShield ML Pipeline

RuralShield ships a lightweight TF-IDF + binary logistic-regression classifier designed to fit comfortably inside an AWS Lambda package. The trainer is implemented in pure Python so training and inference use the same feature/tokenization semantics without requiring scikit-learn at Lambda runtime.

`train.py` accepts a CSV containing `text` and `label` columns (`safe` or `phishing`), performs a deterministic stratified train/validation/test split, builds TF-IDF features, trains logistic regression with L2 regularization, writes `backend/lambda/model.json`, and writes `ml/evaluation.json`.

## Bundled demo dataset

`ml/data/demo_dataset.csv` contains **40 synthetic DEMO DATA rows**: 20 safe and 20 phishing. It exists so the complete project can be trained, tested, and demonstrated without private customer data or a dataset-license dependency.

It is **not** a research benchmark and must not be used to claim production detection accuracy. For a serious evaluation, replace it with a legitimate, license-compatible public phishing/SMS/email corpus and document the exact source/version, redistribution terms, class counts, filtering, deduplication, and split methodology.

## Reproduce the model

```bash
python ml/train.py
```

The committed artifact is deterministic for the bundled dataset. CI retrains it and fails if either `backend/lambda/model.json` or `ml/evaluation.json` drifts from the generated files.

Current held-out results on the tiny bundled demo set are recorded in `ml/evaluation.json`. Validation and test each contain six rows. Both currently report 0.8333 accuracy, 1.0 phishing precision, 0.6667 phishing recall, and 0.8 phishing F1. These numbers have very high uncertainty because each held-out split is tiny.

## Component comparison

Run:

```bash
python ml/evaluate_hybrid.py
```

This writes `ml/hybrid_evaluation.json` and compares the deterministic detector variants using the project's `>65 = phishing` system threshold. On the 40-row bundled demo corpus the current results are:

| Variant | Accuracy | Phishing precision | Phishing recall | Phishing F1 |
| --- | ---: | ---: | ---: | ---: |
| Rule only | 0.525 | 0.6667 | 0.10 | 0.1739 |
| ML only | 0.925 | 1.0 | 0.85 | 0.9189 |
| ML + rules | 0.875 | 1.0 | 0.75 | 0.8571 |
| ML + rules + URL | 0.775 | 1.0 | 0.55 | 0.7097 |

This comparison is intentionally reported even though the hybrid variants do **not** win. It is evidence that the initial component weights and system thresholds should not be tuned from this tiny synthetic corpus. It also helped identify and fix a fusion bug where a missing URL was previously counted as a zero-risk URL signal; unavailable signals are now excluded and remaining weights are renormalized.

The full Bedrock-assisted hybrid is not called during offline evaluation because doing so would make CI depend on AWS credentials, network availability, model access, cost, and nondeterministic model output. Bedrock remains an optional contextual/explanation signal at runtime; the ML/rule/URL detector continues to function if Bedrock fails.

## Evaluation requirements for a larger dataset

Report accuracy, per-class precision/recall/F1, confusion matrices, phishing false negatives, and safe-message false positives. Keep one untouched final test set. Tune model parameters, fusion weights, and the SAFE/SUSPICIOUS/PHISHING thresholds only on training/validation data. Compare rule-only, ML-only, ML+rules, ML+rules+URL, and—where an authorized AWS evaluation environment is available—the full hybrid on the same examples.
