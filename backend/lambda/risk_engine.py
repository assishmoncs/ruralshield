from config import (
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


def confidence_level(score: float, *, component_count: int) -> str:
    """Qualitative decision-strength indicator, not a probability."""
    distance = abs(score - 50.0)
    if component_count >= 3 and distance >= 30:
        return "HIGH"
    if component_count >= 2 and distance >= 15:
        return "MEDIUM"
    return "LOW"


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
    """Fuse deterministic security signals.

    Amazon Bedrock is intentionally excluded from the security decision. It is
    treated as an explanation/context layer so an LLM cannot directly override
    deterministic phishing evidence.
    """
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
    }

    active = ["rules"]
    if ml_available:
        active.insert(0, "ml")
    if url_available:
        active.append("url")

    denominator = sum(weights[name] for name in active) or 1.0
    score = sum(values[name] * weights[name] for name in active) / denominator
    score = round(max(0.0, min(100.0, score)), 2)

    return {
        "risk_score": score,
        "classification": classify(score),
        "confidence_level": confidence_level(score, component_count=len(active)),
        "decision_basis": "ml_rules_url",
        "components": values,
        "weights_used": {
            name: round(weights[name] / denominator, 4) for name in active
        },
        "ai_available": bool(ai_available),
        "ai_used_for_decision": False,
    }
