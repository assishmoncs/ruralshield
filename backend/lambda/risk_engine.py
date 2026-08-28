from config import (
    AI_WEIGHT,
    ML_WEIGHT,
    RULE_WEIGHT,
    SAFE_MAX,
    SUSPICIOUS_MAX,
    URL_WEIGHT,
)


def classify(score: float) -> str:
    if score <= SAFE_MAX:
        return "SAFE"
    if score <= SUSPICIOUS_MAX:
        return "SUSPICIOUS"
    return "PHISHING"


def combine_scores(
    ml_score: float,
    url_score: float,
    rule_score: float,
    ai_score: float = 0.0,
    *,
    ml_available: bool = True,
    url_available: bool = True,
    ai_available: bool = True,
):
    values = {
        "ml": max(0.0, min(100.0, ml_score)),
        "url": max(0.0, min(100.0, url_score)),
        "rules": max(0.0, min(100.0, rule_score)),
        "ai": max(0.0, min(100.0, ai_score)),
    }
    weights = {
        "ml": ML_WEIGHT,
        "url": URL_WEIGHT,
        "rules": RULE_WEIGHT,
        "ai": AI_WEIGHT,
    }
    active = ["rules"]
    if ml_available:
        active.insert(0, "ml")
    if url_available:
        active.append("url")
    if ai_available:
        active.append("ai")

    denominator = sum(weights[name] for name in active) or 1.0
    score = sum(values[name] * weights[name] for name in active) / denominator
    score = round(score, 2)
    return {
        "risk_score": score,
        "classification": classify(score),
        "components": values,
        "weights_used": {
            name: round(weights[name] / denominator, 4) for name in active
        },
    }
