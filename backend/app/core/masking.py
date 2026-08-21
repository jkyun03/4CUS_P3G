import re
from app.mcp_tools.registry import PATIENTS


RRN_PATTERN = re.compile(r"\d{6}-\d{7}")
PHONE_PATTERN = re.compile(r"01[016789]-?\d{3,4}-?\d{4}")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

HIDDEN_MARK = "[접근불가]"
DEIDENT_MARK = "[비식별]"


def _mask_person(value: str) -> str:
    if len(value) < 2:
        return value
    return value[0] + "*" * (len(value) - 1)


def _mask_rrn_partial(value: str) -> str:
    m = re.match(r"(\d{6})-?(\d{7})", value)
    if not m:
        return DEIDENT_MARK
    return f"{m.group(1)}-{'*' * 7}"                   


def _mask_phone_partial(value: str) -> str:
    m = re.match(r"(01[016789])-?(\d{3,4})-?(\d{4})", value)
    if not m:
        return DEIDENT_MARK
    return f"{m.group(1)}-{'*' * len(m.group(2))}-{m.group(3)}"   


def _mask_patient_id_partial(value: str) -> str:
    if len(value) <= 3:
        return value
    return value[:2] + "*" * (len(value) - 2)           



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
    return DEIDENT_MARK



FIELD_POLICY = {
    "doctor": {
        "name": "full", "rrn": "partial", "phone": "full",
        "diagnosis": "full", "content": "full",
        "next_appointment": "full", "patient_id": "full",
    },
    "doctor_not_owner": {
        "name": "partial", "rrn": "full_mask", "phone": "full_mask",
        "diagnosis": "full_mask", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "full",
    },
    "nurse": {
        "name": "full", "rrn": "partial", "phone": "full",
        "diagnosis": "full", "content": "full",
        "next_appointment": "full", "patient_id": "full",
    },
    "nurse_not_owner": {
        "name": "partial", "rrn": "full_mask", "phone": "full_mask",
        "diagnosis": "full_mask", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "full",
    },
    "pharmacist": {
        "name": "full", "rrn": "full_mask", "phone": "full_mask",
        "diagnosis": "full", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "full",
    },
    "admin_staff": {
        "name": "full", "rrn": "partial", "phone": "full",
        "diagnosis": "full_mask", "content": "full_mask",
        "next_appointment": "full", "patient_id": "full",
    },
    "insurance_reviewer": {
        "name": "partial", "rrn": "full_mask", "phone": "partial",
        "diagnosis": "full", "content": "full",
        "next_appointment": "hidden", "patient_id": "full",
    },
    "security_officer": {
        "name": "partial", "rrn": "full_mask", "phone": "partial",
        "diagnosis": "full_mask", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "partial",
    },
    "system_admin": {
        "name": "full_mask", "rrn": "full_mask", "phone": "full_mask",
        "diagnosis": "full_mask", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "full",
    },
    "intern": {
        "name": "partial", "rrn": "full_mask", "phone": "full_mask",
        "diagnosis": "full", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "partial",
    },
    "hospital_admin": {
        "name": "full_mask", "rrn": "full_mask", "phone": "full_mask",
        "diagnosis": "full_mask", "content": "full_mask",
        "next_appointment": "hidden", "patient_id": "full",
    },
}

DEFAULT_POLICY = {
    "name": "full_mask", "rrn": "full_mask", "phone": "full_mask",
    "diagnosis": "full_mask", "content": "full_mask",
    "next_appointment": "hidden", "patient_id": "full_mask",
}



def _is_own_patient(role: str, user_id: str, patient_id: str) -> bool:
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
    if role in ("doctor", "nurse") and patient_id:
        if _is_own_patient(role, user_id, patient_id):
            return role
        return f"{role}_not_owner"
    return role



def _scan_free_text(value: str) -> str:
    value = RRN_PATTERN.sub(lambda m: m.group()[:7] + "*******", value)
    value = PHONE_PATTERN.sub("010-****-****", value)
    value = EMAIL_PATTERN.sub(lambda m: m.group()[0] + "***@***", value)
    return value



def mask_data(data, role: str = "hospital_admin", user_id: str = ""):
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
                new_data[k] = _scan_free_text(v)
            else:
                new_data[k] = v
        return new_data

    if isinstance(data, list):
        return [mask_data(item, role, user_id) for item in data]

    return data
    