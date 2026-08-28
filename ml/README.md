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

The trainer is deterministic for the bundled dataset. CI validates the generated artifact structure, model metadata, dataset consistency, and hybrid-decision metadata rather than requiring a brittle byte-for-byte artifact match. Formatting-only JSON changes therefore do not fail CI, while structural corruption still does.

Current held-out results on the tiny bundled demo set are recorded in `ml/evaluation.json`. Validation and test each contain six rows. Both currently report 0.8333 accuracy, 1.0 phishing precision, 0.6667 phishing recall, and 0.8 phishing F1. These numbers have very high uncertainty because each held-out split is tiny.

## Component comparison

Run:

```bash
python ml/evaluate_hybrid.py
```

This writes `ml/hybrid_evaluation.json` and compares deterministic detector variants using the project's `>65 = phishing` system threshold. Bedrock is deliberately excluded from the security decision and therefore from the numeric offline benchmark.

On the 40-row bundled demo corpus the current results are:

| Variant | Accuracy | Phishing precision | Phishing recall | Phishing F1 |
| --- | ---: | ---: | ---: | ---: |
| Rule only | 0.55 | 1.0 | 0.10 | 0.1818 |
| ML only | 0.925 | 1.0 | 0.85 | 0.9189 |
| ML + rules | 0.875 | 1.0 | 0.75 | 0.8571 |
| ML + rules + URL | 0.75 | 1.0 | 0.50 | 0.6667 |

This comparison is intentionally reported even though the hybrid variants do **not** win. It is evidence that the initial component weights and thresholds should not be tuned from this tiny synthetic corpus. It also verifies that missing URL/AI components are excluded rather than treated as zero-risk evidence.

## Production-data path

For a serious model release, prepare a larger, licensed corpus externally and pass its path explicitly:

```bash
python ml/train.py --data path/to/dataset.csv
```

The accepted schema is:

```csv
text,label
Example legitimate message,safe
Example phishing message,phishing
```

Before training, the dataset should undergo:

1. schema and label validation
2. duplicate/near-duplicate review
3. leakage checks before splitting
4. class-distribution analysis
5. stratified train/validation/test splitting
6. threshold and hyperparameter tuning on training/validation only
7. final evaluation once on an untouched test set

A model should be released only with its dataset source/version, license, preprocessing description, metrics, and model version documented in the model card.

## Metrics that matter

Report accuracy, per-class precision/recall/F1, confusion matrices, phishing false negatives, safe-message false positives, and—when enough representative data exists—PR-AUC/ROC-AUC and calibration quality. For phishing detection, recall and false negatives are especially important.

## Bedrock evaluation policy

Do not call Amazon Bedrock during normal CI evaluation. A Bedrock benchmark is nondeterministic, costs money, depends on AWS permissions/model access, and can make CI unreliable. Runtime tests mock the service and verify response validation/fallback behavior. A controlled cloud evaluation can be run separately when an authorized AWS test environment is available.
