import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "lambda"))

from ml_predictor import predict_risk
from risk_engine import classify
from rules import evaluate_rules
from url_analyzer import analyze_url

ML_WEIGHT = 0.40
URL_WEIGHT = 0.25
RULE_WEIGHT = 0.20
PHISHING_THRESHOLD = 65
URL_PATTERN = re.compile(r"(?i)\b((?:https?://|www\.)[^\s<>]+)")


def read_rows(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            label = row.get("label", "").strip().lower()
            if label in {"safe", "phishing"}:
                rows.append((row.get("text", ""), 1 if label == "phishing" else 0))
    return rows


def first_url(text):
    match = URL_PATTERN.search(text or "")
    return match.group(1).rstrip(".,);]") if match else ""


def weighted_score(components, weights):
    denominator = sum(weights.values()) or 1.0
    return sum(components[name] * weights[name] for name in weights) / denominator


def binary_metrics(labels, scores):
    true_positive = true_negative = false_positive = false_negative = 0
    for label, score in zip(labels, scores, strict=True):
        prediction = 1 if score > PHISHING_THRESHOLD else 0
        if label == 1 and prediction == 1:
            true_positive += 1
        elif label == 0 and prediction == 0:
            true_negative += 1
        elif label == 0 and prediction == 1:
            false_positive += 1
        else:
            false_negative += 1

    total = max(1, true_positive + true_negative + false_positive + false_negative)
    precision = true_positive / max(1, true_positive + false_positive)
    recall = true_positive / max(1, true_positive + false_negative)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "accuracy": round((true_positive + true_negative) / total, 4),
        "precision_phishing": round(precision, 4),
        "recall_phishing": round(recall, 4),
        "f1_phishing": round(f1, 4),
        "confusion_matrix": {
            "tn": true_negative,
            "fp": false_positive,
            "fn": false_negative,
            "tp": true_positive,
        },
    }


def evaluate(rows):
    labels = []
    scores = {
        "rule_only": [],
        "ml_only": [],
        "ml_rules": [],
        "ml_rules_url": [],
    }
    for text, label in rows:
        labels.append(label)
        ml_score = predict_risk(text)["score"]
        rule_score = evaluate_rules(text)["score"]
        url = first_url(text)
        url_score = analyze_url(url)["score"] if url else 0.0
        components = {"ml": ml_score, "rules": rule_score, "url": url_score}
        scores["rule_only"].append(rule_score)
        scores["ml_only"].append(ml_score)
        scores["ml_rules"].append(weighted_score(components, {"ml": ML_WEIGHT, "rules": RULE_WEIGHT}))
        active_weights = {"ml": ML_WEIGHT, "rules": RULE_WEIGHT}
        if url:
            active_weights["url"] = URL_WEIGHT
        scores["ml_rules_url"].append(weighted_score(components, active_weights))

    return {
        "dataset_rows": len(rows),
        "decision_threshold": PHISHING_THRESHOLD,
        "classification_rule": "Scores above 65 are phishing for this offline benchmark; lower scores are non-phishing.",
        "decision_architecture": {
            "security_authority": "ml_rules_url",
            "bedrock_in_decision": False,
            "bedrock_role": "contextual explanation only",
        },
        "results": {name: binary_metrics(labels, values) for name, values in scores.items()},
        "full_hybrid": {
            "evaluated": True,
            "numeric_equivalent_to": "ml_rules_url",
            "reason": "Bedrock is intentionally excluded from the security score. Offline evaluation therefore measures the deterministic security path; Bedrock explanation is tested separately.",
        },
        "limitations": "The bundled dataset is synthetic demo data and is too small to support production claims or final threshold tuning.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="ml/data/demo_dataset.csv")
    parser.add_argument("--out", default="ml/hybrid_evaluation.json")
    args = parser.parse_args()
    report = evaluate(read_rows(args.data))
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
