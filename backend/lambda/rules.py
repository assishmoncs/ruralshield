import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RuleHit:
    rule_id: str
    reason: str
    severity: str
    contribution: int


RULES = [
    ("OTP_REQUEST", r"\b(otp|one[- ]?time password)\b", "Requests an OTP", "high", 22),
    ("PIN_REQUEST", r"\b(pin|mpin|upi pin)\b", "Requests a PIN", "high", 24),
    ("PASSWORD_REQUEST", r"\b(password|passcode)\b", "Requests a password", "high", 24),
    ("ACCOUNT_THREAT", r"\b(account|card|upi).{0,35}\b(block|blocked|suspend|suspended|freeze|deactivat)", "Threatens account or service suspension", "high", 18),
    ("URGENT_LANGUAGE", r"\b(urgent|immediately|within \d+ (?:minutes?|hours?)|act now|last warning|verify now)\b", "Uses urgent or pressuring language", "medium", 10),
    ("FAKE_KYC", r"\b(kyc|re-kyc|know your customer).{0,30}\b(update|expire|pending|verify|complete)", "Uses KYC verification pressure", "high", 16),
    ("PAYMENT_DEMAND", r"\b(pay|payment|send|transfer).{0,25}\b(rs\.?|₹|inr|rupees|upi)\b", "Demands a payment or transfer", "medium", 12),
    ("LOTTERY_REWARD", r"\b(lottery|winner|won|reward|cash prize|gift)\b", "Promises an unexpected reward", "medium", 14),
    ("FAKE_REFUND", r"\b(refund|cashback).{0,35}\b(click|claim|verify|process)\b", "Uses a refund or cashback lure", "medium", 13),
    ("LOAN_SCAM", r"\b(pre[- ]?approved loan|instant loan|loan approved|loan offer)\b", "Uses an unsolicited loan offer", "medium", 12),
    ("FAKE_SUPPORT", r"\b(customer care|support team|helpline|bank officer)\b", "Claims to be customer support", "medium", 10),
    ("IMPERSONATION", r"\b(sbi|state bank|hdfc|icici|axis bank|kotak|rbi|bank of baroda|canara bank|union bank)\b", "Uses bank or regulator identity language", "low", 7),
    ("CREDENTIAL_REQUEST", r"\b(card number|cvv|expiry date|account number|netbanking|login credential)\b", "Requests sensitive banking information", "high", 24),
]

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s]+")


def evaluate_rules(text: str):
    lowered = (text or "").lower()
    hits = []
    for rule_id, pattern, reason, severity, contribution in RULES:
        if re.search(pattern, lowered, re.IGNORECASE | re.DOTALL):
            hits.append(RuleHit(rule_id, reason, severity, contribution))
    if URL_RE.search(text or ""):
        hits.append(RuleHit("CONTAINS_URL", "Contains a URL that should be checked", "low", 7))
    score = min(100, sum(hit.contribution for hit in hits))
    return {"score": score, "hits": [asdict(hit) for hit in hits]}
