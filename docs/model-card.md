# RuralShield ML Model Card

## Model

- Model: TF-IDF + binary logistic regression
- Current model version: `1.1.0`
- Runtime: pure Python inference in AWS Lambda
- Purpose: estimate phishing risk from message text as one input to the deterministic RuralShield risk engine

## Intended use

The model is intended for educational and research-oriented phishing-risk decision support for SMS-style banking scam detection. It is not a bank fraud engine, an identity-verification system, or a guarantee against phishing.

## Training data

The repository currently ships a 40-row synthetic demo corpus so the complete application can be trained and tested without redistributing third-party data. This corpus is useful for smoke tests and demonstrations only.

For credible performance claims, train against a sufficiently large, licensed, representative corpus and record the exact dataset version, preprocessing, class distribution, deduplication procedure, split strategy, and random seed. The repository also includes a preparation script for a CC-BY-4.0 Mendeley SMS phishing corpus; see `ml/data/README.md` for provenance and usage details.

## Features

The classifier uses normalized TF-IDF text features with sub-linear term frequency and L2-regularized logistic regression. Tokenization is Unicode-aware so non-Latin text is not discarded during inference; the current vocabulary is still trained from the bundled English-centric demo corpus, so multilingual ML accuracy is not established.

## Decision role

The model does **not** make the final security decision by itself. Its score is fused with deterministic rule and passive URL signals. Amazon Bedrock is used for contextual explanation and recommendations, but its generated risk score is deliberately excluded from the security classification path.

## Evaluation

The bundled evaluation metrics are intentionally labeled as demo-only. The held-out validation/test sets are extremely small, so their uncertainty is high. Do not interpret those numbers as real-world phishing detection performance.

The required evaluation protocol for a larger corpus is:

1. Deduplicate near-identical content before splitting.
2. Keep an untouched final test set.
3. Tune model parameters and security thresholds only on training/validation data.
4. Report accuracy, precision, recall, F1, confusion matrix, phishing false negatives, and safe-message false positives.
5. Add precision-recall and calibration analysis for the model probability.
6. Evaluate adversarial, code-mixed, multilingual, and paraphrased examples separately.

## Known limitations

- The current demo corpus is too small for production claims.
- Text-only lexical models can miss novel or semantically subtle attacks.
- The current vocabulary is not a validated multilingual model.
- Model probabilities are not presented as calibrated confidence; the UI uses a qualitative decision-strength indicator instead.
- URL reputation and ownership are not established by structural analysis alone.

## Safety and privacy

RuralShield does not intentionally persist raw submitted message bodies. Scan records contain derived metadata and a sanitized content hash. The UI warns users not to submit real OTPs, PINs, passwords, or complete card details.

## Versioning and reproducibility

Every trained artifact and scan result records the model version. The bundled demo training procedure is deterministic for the current dataset and seed. CI validates the generated artifact schema and consistency rather than relying on fragile byte-for-byte JSON comparisons. A serious external model release should additionally pin the dataset version and publish the reproducibility manifest.
