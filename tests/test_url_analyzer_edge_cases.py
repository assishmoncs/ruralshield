"""Regression checks for passive URL parsing edge cases."""
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "backend" / "lambda" / "url_analyzer.py"
SPEC = importlib.util.spec_from_file_location("ruralshield_url_analyzer", MODULE_PATH)
URL_ANALYZER = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(URL_ANALYZER)
analyze_url = URL_ANALYZER.analyze_url


def test_brand_word_in_path_is_not_treated_as_a_host_brand():
    result = analyze_url("https://regular.example/help?sbi=verify")
    assert result["features"]["bank_brand_signals"] == []
    assert not any("bank brand" in reason for reason in result["reasons"])


def test_brand_word_in_hostname_is_reported():
    result = analyze_url("https://secure-sbi-login.example")
    assert "sbi" in result["features"]["bank_brand_signals"]
    assert any("bank brand" in reason for reason in result["reasons"])


def test_malformed_bracketed_url_returns_a_risk_signal():
    result = analyze_url("https://[")
    assert result["features"]["malformed_url"] is True
    assert result["score"] >= 30
    assert result["reasons"]


def test_empty_url_is_handled_without_an_exception():
    result = analyze_url("")
    assert result["score"] == 0
    assert result["features"] == {}
    assert result["reasons"] == []
