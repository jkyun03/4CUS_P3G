"""
Mock(가짜) MCP 도구 모음.

실제 병원 시스템 대신, 여기 정의된 함수들이 도구 역할을 한다.
가짜 환자 데이터도 여기에 둔다(나중에 진짜 DB 테이블로 옮길 수 있음).
"""

# ---------------------------------------------------------------------------
# 가짜 환자 30명을 자동 생성한다.
# 이름/진단명/담당의/담당간호사 "목록"만 관리하면 되고,
# 사람 수를 늘리고 싶으면 NAMES 리스트에 이름만 추가하면 된다.
#
# P1001(김민수) -> doctor_kim / nurse_lee
# P1002(이영희) -> doctor_park / nurse_choi
# 이 두 명은 예전 코드와 동일하게 맞춰뒀다 (기존 테스트 코드가 깨지지 않도록).
# ---------------------------------------------------------------------------

NAMES = [
    "김민수", "이영희", "박철수", "최지우", "정하은", "강도현", "윤서연", "임재현",
    "한소희", "오준영", "서지훈", "황유진", "신동욱", "권나연", "장민재", "송예은",
    "홍성민", "배수아", "문상우", "노윤아", "안지호", "유나연", "조현우", "백서진",
    "남궁민", "구본석", "표유정", "탁승현", "여진구", "선우빈", "백서이", "윤자경",
    "권유진", "김서희", "손규하", "박지혜", "박세은", "진우현", "문수연", "강주현",
    "정세형", "심예솔", "이유민", "이나은", "이규민", "강성훈", "김철민", "방혁진",
    "이상욱", "나유진", "유정원", "한채민", "최아리", "유예진", "윤예현", "김민서", 
    "김지영", "강하은", "이수빈", "김가윤", "차주영", "이채연", "김가은", "김태희", 
    "정지수", "정은수", "임세현", "윤현빈", "김호준", "문지훈", "공남균", "도지우", 
    "신승우", "조현빈", "허지윤", "강연지", "홍다현", "유정민", "임예빈", "홍서연",
    "이수민", "김수민", "장은성", "김리윤", "이재혁", "황원휘", "황지환", "이은유",
    "송민서", "조경호", "박준현", "김규령", "유태형", "황석현", 
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
    pid = f"P{1001 + i}"                          # P1001, P1002, ... P1030
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
    return {"status": "sent", "to": to}


def export_csv(**_):
    return {"status": "exported", "file": "records.csv"}


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
