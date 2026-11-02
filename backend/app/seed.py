"""
초기 도구 목록을 DB에 넣는다
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
    {"name": "search",             "role": "FHIR 리소스 검색", "base_risk": "medium", "enabled": True,
     "allowed_roles": ALL_ROLES},
    {"name": "read",               "role": "FHIR 리소스 조회", "base_risk": "medium", "enabled": True,
     "allowed_roles": ALL_ROLES},
    {"name": "create",             "role": "FHIR 리소스 생성", "base_risk": "high", "enabled": True,
     "allowed_roles": ALL_ROLES},
    {"name": "update",             "role": "FHIR 리소스 수정", "base_risk": "high", "enabled": True,
     "allowed_roles": ALL_ROLES},
    {"name": "delete",             "role": "FHIR 리소스 삭제", "base_risk": "high", "enabled": True,
     "allowed_roles": ALL_ROLES},
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
                row.description = description
                row.baseline_description = description
                session.add(row)
        session.commit()


def seed_thresholds():
    with Session(engine) as s:
        if not s.get(PolicyThreshold, 1):
            s.add(PolicyThreshold(id=1))
            s.commit()
