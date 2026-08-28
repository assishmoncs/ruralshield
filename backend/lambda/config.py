import os

ML_WEIGHT = float(os.getenv("ML_WEIGHT", "0.40"))
URL_WEIGHT = float(os.getenv("URL_WEIGHT", "0.25"))
RULE_WEIGHT = float(os.getenv("RULE_WEIGHT", "0.20"))
AI_WEIGHT = float(os.getenv("AI_WEIGHT", "0.15"))  # retained for backward-compatible configuration; not used for security decisions
SAFE_MAX = int(os.getenv("SAFE_MAX", "30"))
SUSPICIOUS_MAX = int(os.getenv("SUSPICIOUS_MAX", "65"))
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "5000"))
TABLE_NAME = os.getenv("TABLE_NAME", "")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "http://localhost:8080").split(",") if x.strip()]
ALLOWED_LANGUAGES = {"en", "hi", "ta"}
MODEL_VERSION_FALLBACK = os.getenv("MODEL_VERSION_FALLBACK", "unknown")
