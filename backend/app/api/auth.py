"""
로그인(JWT 발급)과 요청자 신원 확인/관리자 권한 검사 의존성.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlmodel import Session, select
import jwt

from app.database import get_session
from app.models import User
from app.core.auth import verify_password, create_access_token, decode_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_session)):
    user = db.exec(select(User).where(User.username == body.username)).first()
    if not user or not verify_password(body.password, user.hashed_password, user.salt):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다")

    token = create_access_token(role=user.role, user_id=user.user_id, username=user.username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.user_id,
        "display_name": user.display_name,
    }


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다 (Authorization 헤더 없음)")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다. 다시 로그인하세요")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

    return {"role": payload["role"], "user_id": payload["user_id"], "username": payload["username"]}


def require_admin(identity: dict = Depends(get_current_user)) -> dict:
    if identity["role"] not in ("system_admin", "hospital_admin"):
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    return identity
