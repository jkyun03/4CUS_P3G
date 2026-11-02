"""
도구 호출 1건과 직전 호출 이력을 보고 위험 신호(RiskSignal)와 점수를 뽑아내는 규칙 모음.
"""
from dataclasses import dataclass

from app.core import prompt_injection, ml_classifier
from app.mcp_tools.registry import REQUIRED_ARGUMENTS


@dataclass
class RiskSignal:
    pattern: str    # "sensitive_then_send"
    score: int      # 40
    reason: str


INTERNAL_DOMAIN = "hospital.org"

SENSITIVE_READ_TOOLS = {"get_medical_record"}
EXTERNAL_SEND_TOOLS = {"send_email", "export_csv"}
HIGH_RISK_ACTION_TOOLS = SENSITIVE_READ_TOOLS | EXTERNAL_SEND_TOOLS


def _is_external_email(to: str) -> bool:
    return "@" in to and not to.endswith("@" + INTERNAL_DOMAIN)


SENSITIVE_FHIR_RESOURCE_TYPES = {
    "Patient", "Observation", "Condition", "MedicationRequest",
    "AllergyIntolerance", "DiagnosticReport", "Immunization",
    "FamilyMemberHistory", "DocumentReference", "Encounter",
}
FHIR_READ_TOOLS = {"read", "search"}
FHIR_WRITE_TOOLS = {"create", "update"}
FHIR_DESTRUCTIVE_TOOLS = {"delete"}


def _fhir_resource_type(arguments: dict) -> str:
    return str(arguments.get("type") or arguments.get("resource_type") or arguments.get("resourceType") or "")


def _is_sensitive_fhir_read(tool_name: str, arguments: dict) -> bool:
    return tool_name in FHIR_READ_TOOLS and _fhir_resource_type(arguments) in SENSITIVE_FHIR_RESOURCE_TYPES


def analyze(tool_name: str, arguments: dict, user_request: str,
            history_tool_names: list[str],
            history_calls: list[tuple[str, dict]] | None = None) -> list[RiskSignal]:
    signals: list[RiskSignal] = []

    already_read_sensitive = (
        any(t in SENSITIVE_READ_TOOLS for t in history_tool_names)
        or tool_name in SENSITIVE_READ_TOOLS
    )

    if tool_name in SENSITIVE_READ_TOOLS:
        signals.append(RiskSignal("sensitive_read", 25, "민감정보(진료기록) 조회"))

    if tool_name == "send_email" and _is_external_email(arguments.get("to", "")):
        signals.append(RiskSignal("external_send", 30, "외부 도메인으로 이메일 전송"))
    if tool_name == "export_csv":
        signals.append(RiskSignal("external_send", 30, "CSV 파일로 데이터 반출"))

    if tool_name in EXTERNAL_SEND_TOOLS and already_read_sensitive:
        internal_ok = (tool_name == "send_email"
                       and not _is_external_email(arguments.get("to", "")))
        if not internal_ok:
            signals.append(RiskSignal("sensitive_then_send", 40, "민감정보 조회 후 외부 전송 시도"))

    if "예약" in user_request and tool_name in HIGH_RISK_ACTION_TOOLS:
        signals.append(RiskSignal("purpose_mismatch", 25, "요청 목적(예약 확인)과 무관한 도구 호출"))

    read_count = sum(1 for t in history_tool_names if t in SENSITIVE_READ_TOOLS)
    read_count += 1 if tool_name in SENSITIVE_READ_TOOLS else 0
    if read_count >= 3:
        signals.append(RiskSignal("mass_access", 35, f"진료기록 대량 조회 ({read_count}건)"))

    if _is_sensitive_fhir_read(tool_name, arguments):
        signals.append(RiskSignal("fhir_sensitive_read", 25,
                        f"민감 FHIR 리소스 조회: {_fhir_resource_type(arguments)}"))

    if tool_name in FHIR_WRITE_TOOLS:
        signals.append(RiskSignal("fhir_write", 20,
                        f"FHIR 리소스 변경({tool_name}): {_fhir_resource_type(arguments)}"))

    if tool_name in FHIR_DESTRUCTIVE_TOOLS:
        signals.append(RiskSignal("fhir_delete", 50,
                        f"FHIR 리소스 삭제: {_fhir_resource_type(arguments)}"))

    if history_calls is not None:
        fhir_read_count = sum(1 for n, a in history_calls if _is_sensitive_fhir_read(n, a))
        fhir_read_count += 1 if _is_sensitive_fhir_read(tool_name, arguments) else 0
        if fhir_read_count >= 3:
            signals.append(RiskSignal("fhir_mass_access", 35,
                            f"민감 FHIR 리소스 대량 조회 ({fhir_read_count}건)"))

    injection_hits = prompt_injection.scan(user_request) + prompt_injection.scan_value(arguments)
    if injection_hits:
        signals.append(RiskSignal("prompt_injection", 45,
                                   f"프롬프트 인젝션 의심 패턴 탐지 ({len(injection_hits)}건)"))

    is_ml_injection, ml_confidence = ml_classifier.predict(f"{user_request} {arguments}")
    if is_ml_injection:
        signals.append(RiskSignal("ml_injection_judgment", round(ml_confidence * 45),
                                   f"ML 분류기: 프롬프트 인젝션 의심 (확률 {ml_confidence:.0%})"))

    missing_args = [k for k in REQUIRED_ARGUMENTS.get(tool_name, []) if not arguments.get(k)]
    if missing_args:
        signals.append(RiskSignal("missing_required_arguments", 10,
                                   f"필수 인자 누락: {', '.join(missing_args)}"))

    return signals
