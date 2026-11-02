"""
사람 승인(Human-in-the-loop) API: 승인 대기 목록/처리, 만료 처리, WebSocket 실시간 알림.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import Approval, Event
from app.mcp_tools.registry import run_tool
from app.core import prompt_injection
from app.api.auth import require_admin

router = APIRouter()


class ApprovalConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        for ws in list(self.active):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws)


manager = ApprovalConnectionManager()


@router.websocket("/ws/approvals")
async def approvals_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _expire_if_needed(db: Session, ap: Approval) -> Approval:
    if ap.status == "pending":
        exp = ap.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if _now() > exp:
            ap.status = "expired"
            ap.decided_at = _now()
            db.add(ap)
            db.commit()
            db.refresh(ap)
    return ap


@router.get("/approvals")
def list_approvals(status: str | None = None, db: Session = Depends(get_session)):
    query = select(Approval).order_by(Approval.requested_at.desc())
    if status:
        query = query.where(Approval.status == status)
    items = db.exec(query).all()
    return [_expire_if_needed(db, ap) for ap in items]


@router.get("/approvals/{approval_id}")
def get_approval(approval_id: int, db: Session = Depends(get_session)):
    ap = db.get(Approval, approval_id)
    if not ap:
        raise HTTPException(status_code=404, detail="승인 요청을 찾을 수 없음")
    return _expire_if_needed(db, ap)


class DecideRequest(BaseModel):
    decision: str            # "approve" | "reject"


@router.post("/approvals/{approval_id}/decide")
async def decide_approval(approval_id: int, body: DecideRequest,
                    db: Session = Depends(get_session),
                    identity: dict = Depends(require_admin)):
    ap = db.get(Approval, approval_id)
    if not ap:
        raise HTTPException(status_code=404, detail="승인 요청을 찾을 수 없음")

    ap = _expire_if_needed(db, ap)
    if ap.status != "pending":
        raise HTTPException(status_code=409,
                            detail=f"이미 처리된 요청입니다 (상태: {ap.status})")

    if body.decision == "approve":
        result = await run_tool(ap.tool_name, ap.arguments)
        if prompt_injection.scan_value(result):
            result = prompt_injection.redact(result)
        ap.result = result
        ap.status = "approved"
    elif body.decision == "reject":
        ap.status = "rejected"
    else:
        raise HTTPException(status_code=400,
                            detail="decision 은 approve 또는 reject 여야 합니다")

    ap.decided_at = _now()
    ap.decided_by = identity["username"]
    db.add(ap)

    # 감사 로그(Event)에도 최종 결과를 반영한다 — 안 하면 승인/거부 후에도
    # 감사 로그엔 최초 판정("승인 필요")만 영원히 남는다.
    event = db.get(Event, ap.event_id)
    if event:
        event.decision = ap.status
        db.add(event)

    db.commit()
    db.refresh(ap)
    return ap
