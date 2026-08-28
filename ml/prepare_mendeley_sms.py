"""Prepare the Mendeley SMS phishing corpus for RuralShield training.

The source dataset uses LABEL/TEXT columns and labels messages as Ham, Spam,
or Smishing. RuralShield's phishing task deliberately keeps only Ham -> safe
and Smishing -> phishing; generic Spam is excluded because spam is not
synonymous with phishing.

Usage:
    python ml/prepare_mendeley_sms.py --input path/to/dataset.csv \
        --output ml/data/mendeley_smishing.csv

The script never downloads data automatically and never commits the source
corpus. This keeps CI deterministic and leaves licensing/provenance decisions
explicit for the person running the experiment.
"""

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

LABEL_MAP = {
    "ham": "safe",
    "smishing": "phishing",
}


def normalize_text(value):
    value = re.sub(r"\s+", " ", value or "").strip()
    return value


def find_columns(fieldnames):
    normalized = {name.strip().lower(): name for name in fieldnames if name}
    text_key = normalized.get("text") or normalized.get("message")
    label_key = normalized.get("label")
    if not text_key or not label_key:
        raise ValueError("Input CSV must contain TEXT/message and LABEL columns")
    return text_key, label_key


def prepare(input_path: Path, output_path: Path):
    rows = []
    seen = set()
    counts = {"safe": 0, "phishing": 0, "excluded_spam": 0, "duplicate": 0, "empty": 0}

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header")
        text_key, label_key = find_columns(reader.fieldnames)
        for record in reader:
            text = normalize_text(record.get(text_key, ""))
            label = (record.get(label_key, "") or "").strip().lower()
            if not text:
                counts["empty"] += 1
                continue
            mapped = LABEL_MAP.get(label)
            if label == "spam":
                counts["excluded_spam"] += 1
                continue
            if mapped is None:
                continue
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if digest in seen:
                counts["duplicate"] += 1
                continue
            seen.add(digest)
            rows.append((text, mapped))
            counts[mapped] += 1

    if len(rows) < 100:
        raise ValueError("Prepared corpus is unexpectedly small; inspect source data before training")
    if not counts["safe"] or not counts["phishing"]:
        raise ValueError("Prepared corpus must contain both safe and phishing examples")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(["text", "label"])
        writer.writerows(rows)

    manifest = {
        "source": "Mendeley Data f45bkkt8pr.1",
        "source_title": "SMS PHISHING DATASET FOR MACHINE LEARNING AND PATTERN RECOGNITION",
        "source_license": "CC BY 4.0",
        "mapping": {"Ham": "safe", "Smishing": "phishing", "Spam": "excluded"},
        "output_rows": len(rows),
        "counts": counts,
        "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
    }
    manifest_path = output_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="ml/data/mendeley_smishing.csv")
    args = parser.parse_args()
    manifest = prepare(Path(args.input), Path(args.output))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
