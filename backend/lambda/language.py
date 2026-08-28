import re

SCRIPTS = [
    ("hi", re.compile(r"[\u0900-\u097F]")),
    ("bn", re.compile(r"[\u0980-\u09FF]")),
    ("te", re.compile(r"[\u0C00-\u0C7F]")),
    ("ta", re.compile(r"[\u0B80-\u0BFF]")),
    ("ml", re.compile(r"[\u0D00-\u0D7F]")),
    ("kn", re.compile(r"[\u0C80-\u0CFF]")),
]


def detect_language(text: str) -> str:
    value = text or ""
    counts = [(code, len(pattern.findall(value))) for code, pattern in SCRIPTS]
    code, count = max(counts, key=lambda item: item[1], default=("en", 0))
    return code if count > 0 else "en"
