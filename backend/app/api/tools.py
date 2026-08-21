from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import Tool
from app.api.auth import require_admin

router = APIRouter()


@router.get("/tools")
def list_tools(db: Session = Depends(get_session)):
    tools = db.exec(select(Tool)).all()
    return tools


class ToolPatchRequest(BaseModel):
    enabled: bool | None = None
    allowed_roles: list[str] | None = None


@router.patch("/tools/{name}")
def update_tool(name: str, body: ToolPatchRequest, db: Session = Depends(get_session),
                identity: dict = Depends(require_admin)):
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
