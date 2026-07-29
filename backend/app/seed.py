"""
초기 도구 목록을 DB에 넣는다 (서버 시작 시 1회).
"""
from sqlmodel import Session, select

from app.database import engine
from app.models import Tool

ALL_ROLES = ["doctor", "nurse", "pharmacist", "admin_staff", "insurance_reviewer",
             "security_officer", "system_admin", "intern", "hospital_admin"]

DEFAULT_TOOLS = [
    {"name": "search_patient",     "role": "환자 검색",     "base_risk": "low",  "enabled": True,
     "allowed_roles": ALL_ROLES},
    {"name": "get_appointment",    "role": "예약 조회",     "base_risk": "low",  "enabled": True,
     "allowed_roles": ALL_ROLES},
    {"name": "get_medical_record", "role": "진료기록 조회", "base_risk": "high", "enabled": True,
     "allowed_roles": ALL_ROLES},
    {"name": "send_email",         "role": "이메일 발송",   "base_risk": "high", "enabled": True,
     "allowed_roles": ["system_admin"]},
    {"name": "export_csv",         "role": "CSV 반출",      "base_risk": "high", "enabled": False,
     "allowed_roles": ["system_admin"]},
]


def seed_tools() -> None:
    with Session(engine) as session:
        for t in DEFAULT_TOOLS:
            exists = session.exec(select(Tool).where(Tool.name == t["name"])).first()
            if not exists:
                session.add(Tool(**t))
        session.commit()
        