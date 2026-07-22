"""
행동 분석기 (보안 엔진의 핵심).

이번 호출 + 세션의 '이전 호출들(history)'을 함께 보고 위험 신호를 만든다.
=> 단건이 아니라 '행동 흐름'을 본다는 것이 이 프로젝트의 핵심.

이 파일은 FastAPI/DB에 의존하지 않는 순수 파이썬이다.
그래서 서버 없이도 단위 테스트로 검증할 수 있다.
"""
from dataclasses import dataclass


@dataclass
class RiskSignal:
    """위험 신호 하나: 어떤 패턴이 몇 점이고 왜 위험한지."""
    pattern: str    # "sensitive_then_send"
    score: int      # 40
    reason: str     # "민감정보 조회 후 외부 전송 시도"


# 병원 내부 이메일 도메인. 이 밖으로 보내면 '외부 전송'으로 본다.
INTERNAL_DOMAIN = "hospital.org"

SENSITIVE_READ_TOOLS = {"get_medical_record"}          # 민감정보를 읽는 도구
EXTERNAL_SEND_TOOLS = {"send_email", "export_csv"}     # 밖으로 내보내는 도구
HIGH_RISK_ACTION_TOOLS = SENSITIVE_READ_TOOLS | EXTERNAL_SEND_TOOLS


def _is_external_email(to: str) -> bool:
    return "@" in to and not to.endswith("@" + INTERNAL_DOMAIN)


def analyze(tool_name: str, arguments: dict, user_request: str,
            history_tool_names: list[str]) -> list[RiskSignal]:
    """위험 신호 리스트를 반환한다(없으면 빈 리스트)."""
    signals: list[RiskSignal] = []

    # 세션에서 이미 민감정보를 읽었는가?
    already_read_sensitive = (
        any(t in SENSITIVE_READ_TOOLS for t in history_tool_names)
        or tool_name in SENSITIVE_READ_TOOLS
    )

    # 1) 민감정보 조회
    if tool_name in SENSITIVE_READ_TOOLS:
        signals.append(RiskSignal("sensitive_read", 25, "민감정보(진료기록) 조회"))

    # 2) 외부 전송
    if tool_name == "send_email" and _is_external_email(arguments.get("to", "")):
        signals.append(RiskSignal("external_send", 30, "외부 도메인으로 이메일 전송"))
    if tool_name == "export_csv":
        signals.append(RiskSignal("external_send", 30, "CSV 파일로 데이터 반출"))

    # 3) 민감정보 조회 '후' 외부 전송  ← 흐름 기반 탐지의 핵심
    if tool_name in EXTERNAL_SEND_TOOLS and already_read_sensitive:
        internal_ok = (tool_name == "send_email"
                       and not _is_external_email(arguments.get("to", "")))
        if not internal_ok:
            signals.append(RiskSignal("sensitive_then_send", 40, "민감정보 조회 후 외부 전송 시도"))

    # 4) 목적-행동 불일치 (간단 버전): 예약 문의인데 고위험 도구를 호출
    if "예약" in user_request and tool_name in HIGH_RISK_ACTION_TOOLS:
        signals.append(RiskSignal("purpose_mismatch", 25, "요청 목적(예약 확인)과 무관한 도구 호출"))

    # 5) 대량 조회: 이번 포함 진료기록 조회가 3건 이상
    read_count = sum(1 for t in history_tool_names if t in SENSITIVE_READ_TOOLS)
    read_count += 1 if tool_name in SENSITIVE_READ_TOOLS else 0
    if read_count >= 3:
        signals.append(RiskSignal("mass_access", 35, f"진료기록 대량 조회 ({read_count}건)"))

    return signals
