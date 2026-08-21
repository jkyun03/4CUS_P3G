import re

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions", re.I),
    re.compile(r"disregard\s+(the\s+)?(above|previous|prior)", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"system\s*prompt", re.I),
    re.compile(r"reveal\s+your\s+(instructions|system\s*prompt)", re.I),
    re.compile(r"new\s+instructions\s*:", re.I),
    re.compile(r"\bDAN\b"),
    re.compile(r"이전\s*(지시|명령|프롬프트)[를을]?\s*(무시|잊)"),
    re.compile(r"지금부터\s*(너는|당신은)"),
    re.compile(r"시스템\s*프롬프트[를을]?\s*(알려|보여|출력)"),
    re.compile(r"위\s*(지시|명령)[은는을를]?\s*(무시|따르지\s*마)"),
    re.compile(r"역할[을를]?\s*(무시|바꿔|재정의)"),
]

ZERO_WIDTH_PATTERN = re.compile(r"[​‌‍﻿]")

REDACT_MARK = "[차단된 지시문]"


def scan(text) -> list[str]:
    if not isinstance(text, str) or not text:
        return []
    hits = [pat.pattern for pat in INJECTION_PATTERNS if pat.search(text)]
    if ZERO_WIDTH_PATTERN.search(text):
        hits.append("제로폭 문자(숨김 텍스트)")
    return hits


def scan_value(value) -> list[str]:
    if isinstance(value, str):
        return scan(value)
    if isinstance(value, dict):
        hits = []
        for v in value.values():
            hits.extend(scan_value(v))
        return hits
    if isinstance(value, list):
        hits = []
        for v in value:
            hits.extend(scan_value(v))
        return hits
    return []


def redact(value):
    if isinstance(value, str):
        text = ZERO_WIDTH_PATTERN.sub("", value)
        for pat in INJECTION_PATTERNS:
            text = pat.sub(REDACT_MARK, text)
        return text
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value
