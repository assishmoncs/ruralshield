import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "lambda"))

from risk_engine import combine_scores


def test_missing_url_signal_is_not_counted_as_zero_risk():
    with_url = combine_scores(
        90,
        0,
        60,
        0,
        url_available=True,
        ai_available=False,
    )
    without_url = combine_scores(
        90,
        0,
        60,
        0,
        url_available=False,
        ai_available=False,
    )
    assert "url" in with_url["weights_used"]
    assert "url" not in without_url["weights_used"]
    assert without_url["risk_score"] > with_url["risk_score"]


def test_rules_remain_available_when_ml_and_ai_are_unavailable():
    result = combine_scores(
        0,
        0,
        80,
        0,
        ml_available=False,
        url_available=False,
        ai_available=False,
    )
    assert result["risk_score"] == 80
    assert result["weights_used"] == {"rules": 1.0}
    assert result["classification"] == "PHISHING"
