import json
import math
import os
import re
from pathlib import Path

MODEL_PATH = Path(os.getenv("MODEL_PATH", Path(__file__).with_name("model.json")))

_cached = None


def _load_model():
    global _cached
    if _cached is not None:
        return _cached
    try:
        with MODEL_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data.get("vocabulary"), dict) or not isinstance(data.get("weights"), list):
            raise TypeError("invalid model artifact")
        _cached = data
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        _cached = None
    return _cached


def _tokens(text: str):
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def predict_risk(text: str):
    model = _load_model()
    if not model:
        return {"score": 50.0, "probability": 0.5, "available": False, "model": "unavailable"}
    vocab = model["vocabulary"]
    idf = model["idf"]
    weights = model["weights"]
    counts = {}
    for tok in _tokens(text):
        if tok in vocab:
            idx = vocab[tok]
            counts[idx] = counts.get(idx, 0) + 1
    norm_sq = 0.0
    vec = {}
    for idx, count in counts.items():
        tfidf = (1.0 + math.log(count)) * idf[idx]
        vec[idx] = tfidf
        norm_sq += tfidf * tfidf
    norm = math.sqrt(norm_sq) or 1.0
    z = float(model.get("intercept", 0.0))
    for idx, value in vec.items():
        z += (value / norm) * weights[idx]
    prob = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
    return {"score": round(prob * 100, 2), "probability": round(prob, 4), "available": True, "model": model.get("name", "tfidf_logistic_regression")}
