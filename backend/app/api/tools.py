"""
도구 관리 API. ('툴 별 권한 관리' 기능)

- GET   /tools         : 도구 목록 (이름·역할·위험도·on/off·허용 직군)
- PATCH /tools/{name}  : 도구 켜기/끄기, 허용 직군 수정
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import Tool

router = APIRouter()


@router.get("/tools")
def list_tools(db: Session = Depends(get_session)):
    """등록된 도구를 모두 돌려준다."""
    return db.exec(select(Tool).order_by(Tool.id)).all()


class ToolUpdate(BaseModel):
    # 둘 다 선택 사항. 보낸 값만 수정된다.
    enabled: Optional[bool] = None
    allowed_roles: Optional[list[str]] = None


@router.patch("/tools/{name}")
def update_tool(name: str, body: ToolUpdate, db: Session = Depends(get_session)):
    """도구 하나를 수정한다 (켜기/끄기, 허용 직군)."""
    tool = db.exec(select(Tool).where(Tool.name == name)).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"도구를 찾을 수 없음: {name}")

    if body.enabled is not None:
        tool.enabled = body.enabled
    if body.allowed_roles is not None:
        tool.allowed_roles = body.allowed_roles

    db.add(tool)
    db.commit()
    db.refresh(tool)
    return tool