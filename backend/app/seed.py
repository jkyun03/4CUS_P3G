"""
초기 도구 목록을 DB에 넣는다 (서버 시작 시 1회).

이 목록이 '툴 별 권한 관리' 기능의 시작점이다.
- enabled=False : 아예 사용 금지된 도구 (예: export_csv)
- allowed_roles : 이 역할만 호출 가능
나중에 관리자 화면에서 이 값들을 수정하는 API를 붙이면 된다.
"""
from sqlmodel import Session, select

from app.database import engine
from app.models import Tool

DEFAULT_TOOLS = [
    {"name": "search_patient",     "role": "환자 검색",     "base_risk": "low",  "enabled": True,  "allowed_roles": ["doctor", "nurse", "admin"]},
    {"name": "get_appointment",    "role": "예약 조회",     "base_risk": "low",  "enabled": True,  "allowed_roles": ["doctor", "nurse", "admin"]},
    {"name": "get_medical_record", "role": "진료기록 조회", "base_risk": "high", "enabled": True,  "allowed_roles": ["doctor", "admin"]},
    {"name": "send_email",         "role": "이메일 발송",   "base_risk": "high", "enabled": True,  "allowed_roles": ["admin"]},
    {"name": "export_csv",         "role": "CSV 반출",      "base_risk": "high", "enabled": False, "allowed_roles": ["admin"]},
]


def seed_tools() -> None:
    with Session(engine) as session:
        for t in DEFAULT_TOOLS:
            exists = session.exec(select(Tool).where(Tool.name == t["name"])).first()
            if not exists:
                session.add(Tool(**t))
        session.commit()
