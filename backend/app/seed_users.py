# backend/app/seed_users.py
"""
데모 로그인 계정을 만든다 (서버 시작 시 1회).
"""
from sqlmodel import Session, select

from app.database import engine
from app.models import User
from app.core.auth import hash_password

DEMO_USERS = [
    ("doctor_kim", "pass1234", "doctor", "doctor_kim", "김민수 담당의"),
    ("doctor_park", "pass1234", "doctor", "doctor_park", "이영희 담당의"),
    ("nurse_lee", "pass1234", "nurse", "nurse_lee", "김민수 담당간호사"),
    ("nurse_choi", "pass1234", "nurse", "nurse_choi", "이영희 담당간호사"),
    ("pharm01", "pass1234", "pharmacist", "pharm01", "약사"),
    ("admin_staff01", "pass1234", "admin_staff", "admin_staff01", "원무과 직원"),
    ("insurance01", "pass1234", "insurance_reviewer", "insurance01", "보험심사 담당자"),
    ("security01", "pass1234", "security_officer", "security01", "보안 담당자"),
    ("sysadmin01", "pass1234", "system_admin", "sysadmin01", "전산 담당자"),
    ("intern01", "pass1234", "intern", "intern01", "실습생"),
    ("hospadmin01", "pass1234", "hospital_admin", "hospadmin01", "병원 행정직"),
]


def seed_users() -> None:
    with Session(engine) as session:
        for username, password, role, user_id, display_name in DEMO_USERS:
            exists = session.exec(select(User).where(User.username == username)).first()
            if not exists:
                hashed, salt = hash_password(password)
                session.add(User(username=username, hashed_password=hashed, salt=salt,
                                  role=role, user_id=user_id, display_name=display_name))
        session.commit()

