# ML Data Sources

## Bundled demo corpus

`demo_dataset.csv` is a 40-row synthetic corpus used for deterministic local demos and CI. It is intentionally not presented as a production benchmark.

## Recommended external SMS corpus

RuralShield includes `ml/prepare_mendeley_sms.py` to prepare the publicly documented **SMS PHISHING DATASET FOR MACHINE LEARNING AND PATTERN RECOGNITION** from Mendeley Data, DOI `10.17632/f45bkkt8pr.1`.

The source describes 5,971 messages labeled `Ham`, `Spam`, or `Smishing` and is published under **CC BY 4.0**. For RuralShield's phishing task:

- `Ham` → `safe`
- `Smishing` → `phishing`
- `Spam` → excluded

Spam is deliberately excluded from the binary safe/phishing training target because unwanted commercial spam is not equivalent to phishing.

Source: https://data.mendeley.com/datasets/f45bkkt8pr/1

## Preparation

Download the source dataset from Mendeley Data according to its published terms, then run:

```bash
python ml/prepare_mendeley_sms.py --input path/to/source.csv --output ml/data/mendeley_smishing.csv
python ml/train.py --data ml/data/mendeley_smishing.csv
```

The preparation script validates the schema, removes empty rows, removes exact duplicate messages, excludes generic spam, writes the normalized `text,label` CSV, and writes a SHA-256 manifest alongside it.

Do not upload private banking/customer messages. Review redistribution terms before committing any generated dataset file to GitHub. The prepared corpus is intentionally not required by CI; CI remains deterministic using the bundled demo corpus.

## Future dataset expansion

For the strongest evaluation, combine carefully chosen licensed corpora and create a separate untouched test set. Track source, license, language, label mapping, deduplication rules, and dataset version in a manifest. Evaluate English, code-mixed, and Indian-language samples separately rather than assuming one aggregate score represents all users.
