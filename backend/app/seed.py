"""
초기 도구 목록을 DB에 넣는다 (서버 시작 시 1회).
"""
from sqlmodel import Session, select

from app.database import engine
from app.models import Tool, PolicyThreshold
from app.mcp_tools.registry import TOOL_DESCRIPTIONS

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
            description = TOOL_DESCRIPTIONS.get(t["name"], "")
            row = session.exec(select(Tool).where(Tool.name == t["name"])).first()
            if not row:
                data = dict(t, description=description, baseline_description=description)
                session.add(Tool(**data))
            elif not row.description:
                # 설명 필드 도입 전에 만들어진 기존 행 — 설명을 채우고 기준값(baseline)도 함께 기록한다.
                row.description = description
                row.baseline_description = description
                session.add(row)
        session.commit()
        
def seed_thresholds():
    with Session(engine) as s:
        if not s.get(PolicyThreshold, 1):
            s.add(PolicyThreshold(id=1))  # 기본값(30/60/80)으로 한 행 생성
            s.commit()