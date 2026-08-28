import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RuleHit:
    rule_id: str
    reason: str
    severity: str
    contribution: int


REQUEST_VERB = r"(?:share|send|provide|tell|enter|submit|give|confirm|reply|forward|reveal|type|upload)"
OTP_TERM = r"(?:otp|one[- ]?time password)"
PIN_TERM = r"(?:pin|mpin|upi pin)"
PASSWORD_TERM = r"(?:password|passcode|login password|netbanking password)"
CREDENTIAL_TERM = r"(?:card number|cvv|expiry date|account number|netbanking|login credential|banking details)"

RULES = [
    ("OTP_REQUEST", rf"(?:\b{OTP_TERM}\b).{{0,55}}\b{REQUEST_VERB}\b|\b{REQUEST_VERB}\b.{{0,55}}\b{OTP_TERM}\b", "Requests you to disclose an OTP", "high", 24),
    ("PIN_REQUEST", rf"(?:\b{PIN_TERM}\b).{{0,55}}\b{REQUEST_VERB}\b|\b{REQUEST_VERB}\b.{{0,55}}\b{PIN_TERM}\b", "Requests you to disclose a PIN", "high", 26),
    ("PASSWORD_REQUEST", rf"(?:\b{PASSWORD_TERM}\b).{{0,55}}\b{REQUEST_VERB}\b|\b{REQUEST_VERB}\b.{{0,55}}\b{PASSWORD_TERM}\b", "Requests your banking password or passcode", "high", 26),
    ("CREDENTIAL_REQUEST", rf"(?:\b{CREDENTIAL_TERM}\b).{{0,55}}\b{REQUEST_VERB}\b|\b{REQUEST_VERB}\b.{{0,55}}\b{CREDENTIAL_TERM}\b", "Requests sensitive banking information", "high", 26),
    ("ACCOUNT_THREAT", r"\b(account|card|upi|wallet|banking).{0,50}\b(block|blocked|suspend|suspended|freeze|frozen|deactivat|close|terminate)\w*\b", "Threatens account or banking-service suspension", "high", 18),
    ("URGENT_LANGUAGE", r"\b(urgent|immediately|within \d+ (?:minutes?|hours?)|act now|last warning|verify now|today only)\b", "Uses urgent or pressuring language", "medium", 10),
    ("FAKE_KYC", r"\b(kyc|re-kyc|know your customer)\b.{0,45}\b(update|expire|pending|verify|complete|required|submit)\b|\b(update|complete|verify|submit)\b.{0,45}\b(kyc|re-kyc)\b", "Uses KYC verification pressure", "high", 16),
    ("PAYMENT_DEMAND", r"\b(pay|payment|send|transfer|deposit).{0,30}\b(?:rs\.?|₹|inr|rupees|upi|fee|charge|tax)\b|\b(?:rs\.?|₹|inr|rupees)\s?\d+.{0,30}\b(pay|send|transfer)\b", "Demands a payment or transfer", "medium", 12),
    ("LOTTERY_REWARD", r"\b(lottery|winner|won|reward|cash prize|gift|jackpot|cashback)\b.{0,45}\b(claim|pay|fee|charge|click|transfer)\b|\b(claim|pay|fee|charge|click|transfer)\b.{0,45}\b(lottery|reward|prize|jackpot)\b", "Promises an unexpected reward and pushes an action", "medium", 14),
    ("FAKE_REFUND", r"\b(refund|cashback|reversal).{0,45}\b(click|claim|verify|enter|provide|share|pay)\b|\b(click|claim|verify|enter|provide|share|pay)\b.{0,45}\b(refund|cashback|reversal)\b", "Uses a refund or cashback lure", "medium", 13),
    ("LOAN_SCAM", r"\b(pre[- ]?approved loan|instant loan|loan approved|loan offer)\b.{0,45}\b(pay|fee|charge|transfer|share|send)\b|\b(pay|fee|charge|transfer|share|send)\b.{0,45}\b(pre[- ]?approved loan|instant loan|loan approved)\b", "Uses an unsolicited loan offer that requests an action", "medium", 12),
    ("FAKE_SUPPORT", r"\b(customer care|support team|helpline|bank officer|security team)\b.{0,55}\b(call|contact|share|send|provide|tell|install|download|screen|code|otp|pin)\b|\b(call|contact|share|send|provide|tell|install|download|screen|code|otp|pin)\b.{0,55}\b(customer care|support team|helpline|bank officer)\b", "Impersonates customer support and requests an action", "medium", 10),
    ("IMPERSONATION", r"\b(sbi|state bank|hdfc|icici|axis|kotak|rbi|bank of baroda|canara bank|union bank)\b.{0,60}\b(verify|login|update|share|send|provide|click|account|kyc|otp|pin|password)\b", "Uses a bank or regulator identity to pressure an action", "low", 7),
]

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s]+")
MITIGATING_PATTERNS = [
    ("SECURITY_AWARENESS", r"\b(?:never|do not|don't|dont|will never)\b.{0,35}\b(?:share|send|give|tell|provide|enter).{0,20}\b(?:otp|pin|password|cvv|card)\b", "Warns users not to disclose sensitive banking credentials", 12),
    ("OFFICIAL_CHANNEL_ADVICE", r"\b(?:official app|official website|official channel|number on (?:the )?(?:back|rear) of (?:your )?card)\b", "Directs users to an official banking channel", 6),
]


def evaluate_rules(text: str):
    lowered = (text or "").lower()
    hits = []
    for rule_id, pattern, reason, severity, contribution in RULES:
        if re.search(pattern, lowered, re.IGNORECASE | re.DOTALL):
            hits.append(RuleHit(rule_id, reason, severity, contribution))

    if URL_RE.search(text or ""):
        hits.append(RuleHit("CONTAINS_URL", "Contains a URL that should be checked", "low", 5))

    mitigating_hits = []
    mitigation = 0
    for rule_id, pattern, reason, contribution in MITIGATING_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE | re.DOTALL):
            mitigating_hits.append(RuleHit(rule_id, reason, "mitigating", contribution))
            mitigation += contribution

    raw_score = sum(hit.contribution for hit in hits)
    score = max(0, min(100, raw_score - min(20, mitigation)))
    return {
        "score": score,
        "hits": [asdict(hit) for hit in hits],
        "mitigating_hits": [asdict(hit) for hit in mitigating_hits],
        "raw_score": min(100, raw_score),
        "mitigation_points": min(20, mitigation),
    }
