"""
Mock(가짜) MCP 도구 모음.

실제 병원 시스템 대신, 여기 정의된 함수들이 도구 역할을 한다.
가짜 환자 데이터도 여기에 둔다(나중에 진짜 DB 테이블로 옮길 수 있음).
"""

# ---- 가짜 병원 데이터 ---------------------------------------------------
# attending_doctor / attending_nurse : 이 환자를 담당하는 의사/간호사의 user_id.
# 마스킹 단계(app/core/masking.py)에서 "본인 담당 환자인지" 판단할 때 이 값을 사용한다.
PATIENTS = {
    "P1001": {
        "patient_id": "P1001",
        "name": "김민수",
        "rrn": "900101-1234567",
        "phone": "010-1234-5678",
        "attending_doctor": "doctor_kim",
        "attending_nurse": "nurse_lee",
    },
    "P1002": {
        "patient_id": "P1002",
        "name": "이영희",
        "rrn": "880505-2345678",
        "phone": "010-2222-3333",
        "attending_doctor": "doctor_park",
        "attending_nurse": "nurse_choi",
    },
}
RECORDS = {
    "P1001": {"patient_id": "P1001", "diagnosis": "고혈압", "content": "3개월 약물치료 필요"},
    "P1002": {"patient_id": "P1002", "diagnosis": "제2형 당뇨", "content": "식이요법 병행 권장"},
}
APPOINTMENTS = {
    "P1001": {"patient_id": "P1001", "next_appointment": "2026-06-02 10:30"},
    "P1002": {"patient_id": "P1002", "next_appointment": "2026-06-05 14:00"},
}


# ---- 도구 함수들 -------------------------------------------------------
def search_patient(name: str = "", **_):
    for p in PATIENTS.values():
        if p["name"] == name:
            return {"patient_id": p["patient_id"], "name": p["name"]}
    return {"error": "환자를 찾을 수 없음"}


def get_appointment(patient_id: str = "", **_):
    return APPOINTMENTS.get(patient_id, {"error": "예약 정보 없음"})


def get_medical_record(patient_id: str = "", **_):
    return RECORDS.get(patient_id, {"error": "진료기록 없음"})


def send_email(to: str = "", body: str = "", **_):
    return {"status": "sent", "to": to}


def export_csv(**_):
    return {"status": "exported", "file": "records.csv"}


# 도구 이름 -> 실행 함수 매핑
TOOL_FUNCTIONS = {
    "search_patient": search_patient,
    "get_appointment": get_appointment,
    "get_medical_record": get_medical_record,
    "send_email": send_email,
    "export_csv": export_csv,
}


def run_tool(name: str, arguments: dict):
    """이름으로 도구를 찾아 실행한다."""
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"알 수 없는 도구: {name}"}
    return fn(**arguments)
    