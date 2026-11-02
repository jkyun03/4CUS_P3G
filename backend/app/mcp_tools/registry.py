"""
Mock(가짜) MCP 도구 모음.

실제 병원 시스템 대신, 여기 정의된 함수들이 도구 역할을 한다.
가짜 환자 데이터도 여기에 둔다(나중에 진짜 DB 테이블로 옮길 수 있음).
"""

# ---------------------------------------------------------------------------
# 가짜 환자를 NAMES 수만큼(현재 94명) 자동 생성한다.
# 이름은 실존 인물과 무관하게 무작위로 조합한 가상 이름이다.
# 이름/진단명/담당의/담당간호사 "목록"만 관리하면 되고,
# 사람 수를 늘리고 싶으면 NAMES 리스트에 이름만 추가하면 된다.
#
# P1001(김민수) -> doctor_kim / nurse_lee
# P1002(이영희) -> doctor_park / nurse_choi
# 이 두 명은 예전 코드와 동일하게 맞춰뒀다 (기존 테스트 코드가 깨지지 않도록).
# ---------------------------------------------------------------------------

NAMES = [
    "김민수", "이영희", "표한빈", "우고욱", "왕하영", "구래은", "박재주", "진가현",
    "양아찬", "송우하", "배운준", "추경민", "국찬아", "명도니", "임빈우", "장규린",
    "원동한", "차빈윤", "지재은", "추호철", "반건하", "원주경", "마채율", "현아찬",
    "길호서", "염세서", "노가니", "맹호율", "성채람", "도상철", "권승휘", "성해진",
    "양세인", "옥린율", "남상호", "백가주", "선호찬", "한민은", "백래운", "금석람",
    "고원재", "손민진", "손민안", "류세철", "서우원", "강원현", "옥선철", "방빈규",
    "금은찬", "금인채", "현인휘", "최민채", "허준은", "전연철", "표화훈", "홍상석",
    "마규한", "변선한", "채보찬", "공원석", "반찬준", "류소진", "조정나", "주채현",
    "백규은", "남세안", "성운담", "추운안", "정원호", "심가연", "진주휘", "양연나",
    "이세은", "변나하", "오도연", "도휘운", "박유현", "황시호", "모연린", "금건니",
    "지수재", "안래람", "전정람", "장아현", "금호찬", "지호린", "남예담", "반보희",
    "모찬윤", "손찬민", "황채린", "한성원", "백경희", "김윤서",
]

DOCTORS = ["doctor_kim", "doctor_park", "doctor_choi", "doctor_jung"]
NURSES = ["nurse_lee", "nurse_choi", "nurse_kang", "nurse_yoon"]

DIAGNOSES = [
    ("고혈압", "3개월 약물치료 필요"),
    ("제2형 당뇨", "식이요법 병행 권장"),
    ("천식", "흡입기 처방, 3개월 후 재방문"),
    ("골절(우측 손목)", "깁스 착용 중, 6주 경과관찰"),
    ("위염", "제산제 처방, 자극적 음식 제한 권고"),
    ("알레르기 비염", "항히스타민제 처방"),
    ("불면증", "수면 위생 교육 및 약물 상담"),
    ("허리디스크", "물리치료 병행, 통증 조절"),
    ("갑상선기능저하증", "호르몬제 복용 중, 정기 혈액검사 필요"),
    ("편두통", "트립탄 계열 약물 처방"),
]

PATIENTS = {}
RECORDS = {}
APPOINTMENTS = {}

for i, name in enumerate(NAMES):                 # i = 0, 1, 2, ... (0부터 시작)
    pid = f"P{1001 + i}"                          # P1001, P1002, ... P1094
    doctor = DOCTORS[i % len(DOCTORS)]
    nurse = NURSES[i % len(NURSES)]
    diagnosis, content = DIAGNOSES[i % len(DIAGNOSES)]

    PATIENTS[pid] = {
        "patient_id": pid,
        "name": name,
        "rrn": f"{900000 + i:06d}-{1000000 + i:07d}",
        "phone": f"010-{1000 + i:04d}-{5000 + i:04d}",
        "attending_doctor": doctor,
        "attending_nurse": nurse,
    }
    RECORDS[pid] = {
        "patient_id": pid,
        "diagnosis": diagnosis,
        "content": content,
    }
    APPOINTMENTS[pid] = {
        "patient_id": pid,
        "next_appointment": f"2026-06-{(i % 28) + 1:02d} {9 + (i % 8)}:00",
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
    if not to or not body:
        # 수신자/본문이 없으면 '성공'을 거짓으로 알리지 않고 정직하게 실패를 반환한다.
        return {"error": "수신자(to) 또는 본문(body)이 없어 발송하지 않았습니다"}
    return {"status": "sent", "to": to}


def export_csv(**_):
    return {"status": "exported", "file": "records.csv"}


# ---- 도구 설명 (LLM/에이전트에게 그대로 노출되는 텍스트) --------------------
# 툴 포이즈닝 탐지(core/tool_integrity.py)가 이 텍스트를 스캔하고 지문을 남긴다.
TOOL_DESCRIPTIONS = {
    "search_patient": "이름으로 환자를 검색한다. 입력: name(환자 이름).",
    "get_appointment": "환자의 다음 예약 일정을 조회한다. 입력: patient_id.",
    "get_medical_record": "환자의 진료기록(진단명/소견)을 조회한다. 입력: patient_id.",
    "send_email": "지정한 주소로 이메일을 발송한다. 입력: to(수신자), body(본문).",
    "export_csv": "환자 데이터를 CSV 파일로 내보낸다.",
}

# 도구별 필수 인자(비어있으면 안 되는 값). 이게 비어있으면 도구를 아예 실행하지 않고
# "인자 누락"으로 차단한다 — 안 그러면 예: send_email({})처럼 텅 빈 호출도 그냥
# {"status": "sent", "to": ""}로 조용히 '성공' 처리돼버려서, 아무 일도 안 했는데
# 성공한 것처럼 보이는 오해의 소지가 있다.
REQUIRED_ARGUMENTS = {
    "search_patient": ["name"],
    "get_appointment": ["patient_id"],
    "get_medical_record": ["patient_id"],
    "send_email": ["to", "body"],
}


TOOL_FUNCTIONS = {
    "search_patient": search_patient,
    "get_appointment": get_appointment,
    "get_medical_record": get_medical_record,
    "send_email": send_email,
    "export_csv": export_csv,
}


async def run_tool(name: str, arguments: dict):
    # 실제 MCP 서버가 연결돼 있고, 그쪽에 이 도구가 있으면 그쪽으로 위임
    from app.mcp_tools.mcp_client import mcp_client
    if mcp_client.connected and mcp_client.has_tool(name):
        return await mcp_client.call_tool(name, arguments)

    # 아니면 지금까지 쓰던 mock으로 폴백
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"알 수 없는 도구: {name}"}
    return fn(**arguments)
