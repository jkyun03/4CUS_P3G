"""
민감정보 마스킹 유틸리티 — 직군별(role) + 담당 환자 여부(ownership) 기반.

핵심 아이디어:
1. 직군(role)마다 필드별로 "원본(full) / 부분마스킹(partial) / 완전마스킹(full_mask) / 접근불가(hidden)"
   등급이 정해져 있다  (FIELD_POLICY)
2. 단, doctor/nurse는 그 환자가 "본인 담당 환자"일 때만 원래 등급을 적용받고,
   담당 환자가 아니면 훨씬 낮은 등급(doctor_not_owner / nurse_not_owner)으로 강등된다.
3. 정책 표에 없는 role은 안전하게 전부 마스킹(fail-closed).
"""
import re
from app.mcp_tools.registry import PATIENTS

# ---------------------------------------------------------------------------
# 패턴 스캔용 정규식 (필드명으로 못 잡는 자유 텍스트 안의 개인정보용, 기존과 동일)
# ---------------------------------------------------------------------------
RRN_PATTERN = re.compile(r"\d{6}-\d{7}")
PHONE_PATTERN = re.compile(r"01[016789]-?\d{3,4}-?\d{4}")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

HIDDEN_MARK = "[접근불가]"
DEIDENT_MARK = "[비식별]"


# ---------------------------------------------------------------------------
# 필드별 마스킹 함수 (이미지 2 규칙 그대로)
# ---------------------------------------------------------------------------
def _mask_person(value: str) -> str:
    if len(value) < 2:
        return value
    return value[0] + "*" * (len(value) - 1)          # 김민수 -> 김**


def _mask_rrn_partial(value: str) -> str:
    m = re.match(r"(\d{6})-?(\d{7})", value)
    if not m:
        return DEIDENT_MARK
    return f"{m.group(1)}-{'*' * 7}"                    # 900101-1234567 -> 900101-*******


def _mask_phone_partial(value: str) -> str:
    m = re.match(r"(01[016789])-?(\d{3,4})-?(\d{4})", value)
    if not m:
        return DEIDENT_MARK
    return f"{m.group(1)}-{'*' * len(m.group(2))}-{m.group(3)}"   # 010-1234-5678 -> 010-****-5678


def _mask_patient_id_partial(value: str) -> str:
    if len(value) <= 3:
        return value
    return value[:2] + "*" * (len(value) - 2)           # P1001 -> P1***


# ---------------------------------------------------------------------------
# 등급(access level)별 실제 처리 함수
#   "full"      : 원본 그대로
#   "partial"   : 필드별 부분 마스킹 규칙 적용
#   "full_mask" : 완전 비식별
#   "hidden"    : 필드 자체를 숨김
# ---------------------------------------------------------------------------
PARTIAL_MASKERS = {
    "name": _mask_person,
    "rrn": _mask_rrn_partial,
    "phone": _mask_phone_partial,
    "patient_id": _mask_patient_id_partial,
}


def _apply_level(key: str, value: str, level: str) -> str:
    if level == "full":
        return value
    if level == "hidden":
        return HIDDEN_MARK
    if level == "full_mask":
        return DEIDENT_MARK
    if level == "partial":
        masker = PARTIAL_MASKERS.get(key)
        return masker(value) if masker else DEIDENT_MARK
    return DEIDENT_MARK  # 알 수 없는 등급은 안전하게 완전마스킹


# ---------------------------------------------------------------------------
# 직군별 필드 접근 정책 (이미지 1 기준, 교수/연구원 제외 9개 직군)
# doctor_not_owner / nurse_not_owner : 담당 환자가 아닌 의사/간호사에게 적용되는 강등 정책
# ---------------------------------------------------------------------------
FIELD_POLICY = {
    "doctor": {
        "name": "full", "rrn": "partial", "phone": "full",
        "diagnosis": "full", "content": "full",
        "next_appointment": "full", "patient_id": "full",
    },
    "doctor_not_owner": {                      # 담당 환자가 아닌 의사
        "name": "partial", "rrn": "full_mask", "phone": "full_mask",
        "diagnosis": "full_mask", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "full",
    },
    "nurse": {
        "name": "full", "rrn": "partial", "phone": "full",
        "diagnosis": "full", "content": "full",
        "next_appointment": "full", "patient_id": "full",
    },
    "nurse_not_owner": {                        # 담당 환자가 아닌 간호사
        "name": "partial", "rrn": "full_mask", "phone": "full_mask",
        "diagnosis": "full_mask", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "full",
    },
    "pharmacist": {
        "name": "full", "rrn": "full_mask", "phone": "full_mask",
        "diagnosis": "full", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "full",
    },
    "admin_staff": {                             # 원무과 직원
        "name": "full", "rrn": "partial", "phone": "full",
        "diagnosis": "full_mask", "content": "full_mask",
        "next_appointment": "full", "patient_id": "full",
    },
    "insurance_reviewer": {                      # 보험심사 담당자
        "name": "partial", "rrn": "full_mask", "phone": "partial",
        "diagnosis": "full", "content": "full",
        "next_appointment": "hidden", "patient_id": "full",
    },
    "security_officer": {                        # 보안 담당자
        "name": "partial", "rrn": "full_mask", "phone": "partial",
        "diagnosis": "full_mask", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "partial",
    },
    "system_admin": {                            # 전산 담당자
        "name": "full_mask", "rrn": "full_mask", "phone": "full_mask",
        "diagnosis": "full_mask", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "full",
    },
    "intern": {                                   # 실습생
        "name": "partial", "rrn": "full_mask", "phone": "full_mask",
        "diagnosis": "full", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "partial",
    },
    "hospital_admin": {                           # 병원 행정직
        "name": "full_mask", "rrn": "full_mask", "phone": "full_mask",
        "diagnosis": "full_mask", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "full",
    },
}

# 정책 표에 없는(등록 안 된) role에게 적용할 기본값 — fail-closed: 전부 마스킹/숨김
DEFAULT_POLICY = {
    "name": "full_mask", "rrn": "full_mask", "phone": "full_mask",
    "diagnosis": "full_mask", "content": "full_mask",
    "next_appointment": "hidden", "patient_id": "full_mask",
}


# ---------------------------------------------------------------------------
# 담당 환자 여부 판단
# ---------------------------------------------------------------------------
def _is_own_patient(role: str, user_id: str, patient_id: str) -> bool:
    """이 role의 이 user_id가 이 patient_id의 담당자인지 확인한다."""
    if not patient_id or not user_id:
        return False
    patient = PATIENTS.get(patient_id)
    if not patient:
        return False
    if role == "doctor":
        return patient.get("attending_doctor") == user_id
    if role == "nurse":
        return patient.get("attending_nurse") == user_id
    return False


def _resolve_effective_role(role: str, user_id: str, patient_id: str) -> str:
    """doctor/nurse는 담당 환자가 아니면 강등된 role(_not_owner)로 취급한다."""
    if role in ("doctor", "nurse") and patient_id:
        if _is_own_patient(role, user_id, patient_id):
            return role
        return f"{role}_not_owner"
    return role


# ---------------------------------------------------------------------------
# 자유 텍스트(정책 표에 없는 필드) 패턴 스캔 — 기존 로직 그대로 유지
# ---------------------------------------------------------------------------
def _scan_free_text(value: str) -> str:
    value = RRN_PATTERN.sub(lambda m: m.group()[:7] + "*******", value)
    value = PHONE_PATTERN.sub("010-****-****", value)
    value = EMAIL_PATTERN.sub(lambda m: m.group()[0] + "***@***", value)
    return value


# ---------------------------------------------------------------------------
# 메인 진입점
# ---------------------------------------------------------------------------
def mask_data(data, role: str = "hospital_admin", user_id: str = ""):
    """
    dict / list 를 재귀적으로 훑으며, role(+ 담당 환자 여부)에 따라 필드를 가린다.
    role: 요청자의 직군 (doctor, nurse, pharmacist, admin_staff, insurance_reviewer,
          security_officer, system_admin, intern, hospital_admin)
    user_id: 요청자 개인 식별자 (예: "doctor_kim"). doctor/nurse가 담당 환자인지 판단할 때 쓰인다.
    """
    if isinstance(data, dict):
        patient_id = data.get("patient_id")
        effective_role = _resolve_effective_role(role, user_id, patient_id)
        policy = FIELD_POLICY.get(effective_role, DEFAULT_POLICY)

        new_data = {}
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                new_data[k] = mask_data(v, role, user_id)
            elif isinstance(v, str) and k in policy:
                new_data[k] = _apply_level(k, v, policy[k])
            elif isinstance(v, str):
                # 정책 표에 없는 필드(예: error 메시지)는 패턴 스캔만 적용
                new_data[k] = _scan_free_text(v)
            else:
                new_data[k] = v
        return new_data

    if isinstance(data, list):
        return [mask_data(item, role, user_id) for item in data]

    return data
    