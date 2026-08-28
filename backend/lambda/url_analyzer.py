import ipaddress
import math
import re
from collections import Counter
from urllib.parse import unquote, urlparse

SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "rb.gy", "is.gd", "cutt.ly", "shorturl.at"}
BANK_BRANDS = {"sbi", "hdfc", "icici", "axis", "kotak", "canara", "unionbank", "bob", "bankofbaroda", "rbi"}
SUSPICIOUS_WORDS = {"verify", "update", "secure", "login", "kyc", "otp", "refund", "reward", "claim", "unlock", "suspend"}
COMMON_SECOND_LEVEL = {"co", "com", "org", "net", "gov", "ac", "bank"}
COUNTRY_TLDS = {"in", "uk", "au", "nz", "za", "jp", "br"}


def _normalize(raw: str) -> str:
    raw = (raw or "").strip()
    return raw if "://" in raw else "https://" + raw


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _registrable_parts(host: str) -> tuple[str, list[str]]:
    """Conservative offline split for common ccTLD second-level forms."""
    labels = [part for part in host.split(".") if part]
    if len(labels) < 2:
        return host, []
    suffix_len = 1
    if len(labels) >= 3 and labels[-1] in COUNTRY_TLDS and labels[-2] in COMMON_SECOND_LEVEL:
        suffix_len = 2
    registrable_index = max(0, len(labels) - suffix_len - 1)
    return ".".join(labels[registrable_index:]), labels[:registrable_index]


def _idn_signal(host: str) -> bool:
    return "xn--" in host or any(ord(ch) > 127 for ch in host)


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def _domain_entropy(label: str) -> float:
    if not label:
        return 0.0
    counts = Counter(label)
    length = len(label)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def analyze_url(raw: str):
    if not raw:
        return {"score": 0, "features": {}, "reasons": []}
    parsed = urlparse(_normalize(raw))
    host = (parsed.hostname or "").lower().strip(".")
    decoded = unquote(raw)
    registrable, subdomain_labels = _registrable_parts(host)
    subdomains = len(subdomain_labels)
    special_count = len(re.findall(r"[^A-Za-z0-9./:_?=&%-]", raw))
    reasons = []
    points = 0
    if parsed.scheme.lower() != "https":
        reasons.append("The link does not use HTTPS")
        points += 8
    if len(raw) > 90:
        reasons.append("The URL is unusually long")
        points += 10
    if len(host) > 45:
        reasons.append("The website name is unusually long")
        points += 8
    if subdomains >= 3:
        reasons.append("The link uses many subdomains")
        points += min(14, subdomains * 3)
    if "@" in raw:
        reasons.append("The URL contains an @ symbol")
        points += 18
    if decoded != raw or "%" in raw:
        reasons.append("The link contains encoded characters")
        points += 8
    if host and _is_ip(host):
        reasons.append("The link uses an IP address instead of a normal website name")
        points += 22
    if host in SHORTENERS or any(host.endswith("." + s) for s in SHORTENERS):
        reasons.append("The link uses a URL shortener")
        points += 15
    if _idn_signal(host):
        reasons.append("The domain uses internationalized characters that can imitate familiar names")
        points += 18

    lower = decoded.lower()
    keywords = sorted(k for k in SUSPICIOUS_WORDS if k in lower)
    if keywords:
        reasons.append("The link contains risky banking or verification words")
        points += min(18, 4 * len(keywords))

    compact_registrable = re.sub(r"[^a-z0-9]", "", registrable.split(".")[0] if registrable else "")
    brand_hits = sorted(b for b in BANK_BRANDS if b in lower)
    exact_brand_domain = any(compact_registrable == b or compact_registrable == b + "bank" for b in BANK_BRANDS)
    if brand_hits and not exact_brand_domain:
        reasons.append("The link mentions a bank brand in a potentially misleading domain")
        points += 20

    typo_brands = sorted(
        brand for brand in BANK_BRANDS
        if len(brand) >= 4 and compact_registrable != brand and _levenshtein(compact_registrable, brand) == 1
    )
    if typo_brands:
        reasons.append("The domain is one character away from a known banking brand")
        points += 22

    typo_signal = bool(re.search(r"(secure|verify|kyc|login)[-_.]?(sbi|hdfc|icici|axis|kotak)", lower) or re.search(r"(sbi|hdfc|icici|axis|kotak)[-_.]?(secure|verify|kyc|login)", lower))
    if typo_signal:
        reasons.append("The domain pattern resembles bank impersonation")
        points += 15

    primary_label = registrable.split(".")[0] if registrable else host.split(".")[0]
    entropy = _domain_entropy(primary_label)
    randomish = len(primary_label) >= 14 and entropy >= 3.5 and bool(re.search(r"\d", primary_label))
    if randomish:
        reasons.append("The domain name has a high-randomness pattern often seen in disposable links")
        points += 10

    features = {
        "scheme": parsed.scheme.lower(),
        "https": parsed.scheme.lower() == "https",
        "url_length": len(raw),
        "hostname_length": len(host),
        "registrable_domain": registrable,
        "subdomain_count": subdomains,
        "special_character_count": special_count,
        "has_at_symbol": "@" in raw,
        "has_encoding": decoded != raw or "%" in raw,
        "ip_host": bool(host and _is_ip(host)),
        "shortener": host in SHORTENERS or any(host.endswith("." + s) for s in SHORTENERS),
        "idn_or_punycode": _idn_signal(host),
        "suspicious_keywords": keywords,
        "bank_brand_signals": brand_hits,
        "typo_brand_signals": typo_brands,
        "domain_entropy": round(entropy, 3),
        "randomish_domain": randomish,
        "hostname": host,
    }
    return {"score": min(100, points), "features": features, "reasons": reasons}
