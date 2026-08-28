import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "lambda"))

from url_analyzer import analyze_url


def test_indian_second_level_suffix_does_not_inflate_subdomains():
    result = analyze_url("https://secure.example.co.in/login")
    assert result["features"]["registrable_domain"] == "example.co.in"
    assert result["features"]["subdomain_count"] == 1


def test_punycode_is_explicit_risk_signal():
    result = analyze_url("https://xn--sb-7ed.example/verify")
    assert result["features"]["idn_or_punycode"] is True
    assert any("internationalized" in reason for reason in result["reasons"])


def test_one_character_bank_typos_are_flagged():
    result = analyze_url("https://hdfx.example/login")
    assert "hdfc" in result["features"]["typo_brand_signals"]
    assert result["score"] >= 20


def test_high_entropy_numeric_domain_is_flagged():
    result = analyze_url("https://a8f3k9q2m7x4z1.example/verify")
    assert result["features"]["randomish_domain"] is True


def test_normal_domain_is_not_randomish_or_idn():
    result = analyze_url("https://example.org/news")
    assert result["features"]["randomish_domain"] is False
    assert result["features"]["idn_or_punycode"] is False
