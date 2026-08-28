import argparse
import csv
import json
import math
import random
import re
from collections import Counter
from pathlib import Path

SEED = 42


def tokens(text):
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def read_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            label = row.get("label", "").strip().lower()
            if label not in {"safe", "phishing"}:
                continue
            rows.append((row.get("text", ""), 1 if label == "phishing" else 0))
    if len(rows) < 20:
        raise ValueError("Dataset must contain at least 20 labelled rows")
    return rows


def stratified_split(rows, seed=SEED):
    rng = random.Random(seed)
    by_class = {0: [], 1: []}
    for row in rows:
        by_class[row[1]].append(row)
    train, validation, test = [], [], []
    for label_rows in by_class.values():
        rng.shuffle(label_rows)
        count = len(label_rows)
        test_count = max(1, int(count * 0.15))
        validation_count = max(1, int(count * 0.15))
        test += label_rows[:test_count]
        validation += label_rows[test_count : test_count + validation_count]
        train += label_rows[test_count + validation_count :]
    rng.shuffle(train)
    rng.shuffle(validation)
    rng.shuffle(test)
    return train, validation, test


def build_vocab(rows, max_features=6000):
    doc_freq = Counter()
    for text, _ in rows:
        doc_freq.update(set(tokens(text)))
    eligible = [term for term, count in doc_freq.items() if count >= 2]
    terms = sorted(eligible, key=lambda term: (-doc_freq[term], term))[:max_features]
    vocabulary = {term: index for index, term in enumerate(terms)}
    row_count = len(rows)
    idf = [math.log((1 + row_count) / (1 + doc_freq[term])) + 1 for term in terms]
    return vocabulary, idf


def vectorize(text, vocabulary, idf):
    counts = Counter(token for token in tokens(text) if token in vocabulary)
    vector = {}
    norm_sq = 0.0
    for term, count in counts.items():
        index = vocabulary[term]
        value = (1 + math.log(count)) * idf[index]
        vector[index] = value
        norm_sq += value * value
    norm = math.sqrt(norm_sq) or 1.0
    return {index: value / norm for index, value in vector.items()}


def sigmoid(value):
    value = max(-30.0, min(30.0, value))
    return 1 / (1 + math.exp(-value))


def train_logreg(train, vocabulary, idf, epochs=80, learning_rate=0.35, l2=0.0005):
    weights = [0.0] * len(vocabulary)
    intercept = 0.0
    vectors = [(vectorize(text, vocabulary, idf), label) for text, label in train]
    for epoch in range(epochs):
        rate = learning_rate / (1 + epoch * 0.03)
        for vector, label in vectors:
            score = intercept + sum(weights[index] * value for index, value in vector.items())
            error = sigmoid(score) - label
            intercept -= rate * error
            for index, value in vector.items():
                weights[index] -= rate * (error * value + l2 * weights[index])
    return weights, intercept


def metrics(rows, vocabulary, idf, weights, intercept):
    true_positive = true_negative = false_positive = false_negative = 0
    for text, label in rows:
        vector = vectorize(text, vocabulary, idf)
        probability = sigmoid(
            intercept + sum(weights[index] * value for index, value in vector.items())
        )
        prediction = 1 if probability >= 0.5 else 0
        if label == 1 and prediction == 1:
            true_positive += 1
        elif label == 0 and prediction == 0:
            true_negative += 1
        elif label == 0 and prediction == 1:
            false_positive += 1
        else:
            false_negative += 1

    total = max(1, true_positive + true_negative + false_positive + false_negative)
    phishing_precision = true_positive / max(1, true_positive + false_positive)
    phishing_recall = true_positive / max(1, true_positive + false_negative)
    phishing_f1 = 2 * phishing_precision * phishing_recall / max(
        1e-12, phishing_precision + phishing_recall
    )
    safe_precision = true_negative / max(1, true_negative + false_negative)
    safe_recall = true_negative / max(1, true_negative + false_positive)
    safe_f1 = 2 * safe_precision * safe_recall / max(1e-12, safe_precision + safe_recall)
    return {
        "accuracy": round((true_positive + true_negative) / total, 4),
        "precision_phishing": round(phishing_precision, 4),
        "recall_phishing": round(phishing_recall, 4),
        "f1_phishing": round(phishing_f1, 4),
        "precision_safe": round(safe_precision, 4),
        "recall_safe": round(safe_recall, 4),
        "f1_safe": round(safe_f1, 4),
        "confusion_matrix": {
            "tn": true_negative,
            "fp": false_positive,
            "fn": false_negative,
            "tp": true_positive,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="ml/data/demo_dataset.csv")
    parser.add_argument("--model-out", default="backend/lambda/model.json")
    parser.add_argument("--metrics-out", default="ml/evaluation.json")
    args = parser.parse_args()

    rows = read_csv(args.data)
    train, validation, test = stratified_split(rows)
    vocabulary, idf = build_vocab(train)
    weights, intercept = train_logreg(train, vocabulary, idf)
    model = {
        "name": "tfidf_logistic_regression",
        "vocabulary": vocabulary,
        "idf": idf,
        "weights": weights,
        "intercept": intercept,
        "training": {
            "rows": len(rows),
            "train": len(train),
            "validation": len(validation),
            "test": len(test),
            "seed": SEED,
        },
    }
    Path(args.model_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.model_out).write_text(json.dumps(model), encoding="utf-8")

    report = {
        "validation": metrics(validation, vocabulary, idf, weights, intercept),
        "test": metrics(test, vocabulary, idf, weights, intercept),
        "dataset_rows": len(rows),
        "class_distribution": {
            "safe": sum(1 for _, label in rows if label == 0),
            "phishing": sum(1 for _, label in rows if label == 1),
        },
        "split": {
            "train": len(train),
            "validation": len(validation),
            "test": len(test),
            "seed": SEED,
        },
        "note": (
            "Metrics are for the bundled synthetic/demo dataset only; "
            "they are not a production phishing benchmark."
        ),
    }
    Path(args.metrics_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
