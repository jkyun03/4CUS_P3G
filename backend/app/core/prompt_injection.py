"""
프롬프트 인젝션 탐지기.

에이전트(LLM)의 행동을 바꾸려는 지시문 재정의/탈옥(jailbreak) 시도를
아래 세 지점에서 찾는다.
  1. 사용자 요청(user_request)
  2. 도구 호출 인자(arguments)
  3. 도구 실행 '결과' — 간접 인젝션. 공격자가 데이터(진료기록 내용 등) 안에
     지시문을 심어두면, 그 데이터를 읽은 에이전트가 지시로 착각해 따를 수 있다.

core/ 관례대로 FastAPI/DB에 의존하지 않는 순수 파이썬이라 단위 테스트가 쉽다.
"""
import re

# 지시문 재정의/탈옥 시도 패턴 (한국어 + 영어). 정규식 하나 = 시그니처 하나.
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

# 사람 눈에는 안 보이지만 모델은 읽는 제로폭 문자 — 숨김 지시문에 자주 쓰이는 트릭.
ZERO_WIDTH_PATTERN = re.compile(r"[​‌‍﻿]")

REDACT_MARK = "[차단된 지시문]"


def scan(text) -> list[str]:
    """텍스트 하나에서 인젝션 의심 패턴을 찾아 이유 문자열 리스트로 반환한다."""
    if not isinstance(text, str) or not text:
        return []
    hits = [pat.pattern for pat in INJECTION_PATTERNS if pat.search(text)]
    if ZERO_WIDTH_PATTERN.search(text):
        hits.append("제로폭 문자(숨김 텍스트)")
    return hits


def scan_value(value) -> list[str]:
    """dict/list/str 어떤 구조든 재귀적으로 훑어 인젝션 패턴을 모은다 (arguments, 도구 결과용)."""
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
    """
    인젝션 패턴에 매칭된 구간을 마크로 치환한다.
    도구 실행 결과가 에이전트에게 그대로 들어가 지시로 오인되지 않도록 무해화(sanitize)한다.
    """
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
