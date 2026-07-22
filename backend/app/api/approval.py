"""
관리자 승인 API.  ('관리자 승인' 기능)

흐름:
  - /v1/tool_call 이 '승인' 판정을 내리면 Approval 이 pending 으로 만들어진다.
  - 관리자는 GET /approvals?status=pending 으로 대기 목록을 본다.
  - 관리자가 POST /approvals/{id}/decide 로 승인/거부한다.
      승인 -> 이때 도구를 실제로 실행하고 결과를 저장한다.
      거부 -> 상태만 rejected 로 바꾼다.
  - 에이전트는 GET /approvals/{id} 를 반복 조회(poll)하다가
    상태가 approved 가 되면 result 를 받아간다.

제한 시간(expires_at)이 지난 pending 건은 조회/결정 시점에 자동으로 expired 처리한다.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import Approval
from app.mcp_tools.registry import run_tool

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _expire_if_needed(db: Session, ap: Approval) -> Approval:
    """제한 시간이 지난 pending 건이면 expired 로 바꾼다."""
    if ap.status == "pending":
        exp = ap.expires_at
        # SQLite 에서 읽어온 시각은 tz 정보가 없을 수 있어 UTC 로 맞춰준다.
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
    """승인 목록. ?status=pending 으로 대기 건만 볼 수 있다."""
    query = select(Approval).order_by(Approval.requested_at.desc())
    if status:
        query = query.where(Approval.status == status)
    items = db.exec(query).all()
    return [_expire_if_needed(db, ap) for ap in items]


@router.get("/approvals/{approval_id}")
def get_approval(approval_id: int, db: Session = Depends(get_session)):
    """단건 조회. 에이전트가 이걸 반복 호출하며 결정 결과를 기다린다."""
    ap = db.get(Approval, approval_id)
    if not ap:
        raise HTTPException(status_code=404, detail="승인 요청을 찾을 수 없음")
    return _expire_if_needed(db, ap)


class DecideRequest(BaseModel):
    decision: str            # "approve" | "reject"
    admin_id: str = "admin"


@router.post("/approvals/{approval_id}/decide")
def decide_approval(approval_id: int, body: DecideRequest,
                    db: Session = Depends(get_session)):
    """관리자가 승인/거부. 승인이면 여기서 도구를 실행한다."""
    ap = db.get(Approval, approval_id)
    if not ap:
        raise HTTPException(status_code=404, detail="승인 요청을 찾을 수 없음")

    ap = _expire_if_needed(db, ap)
    if ap.status != "pending":
        raise HTTPException(status_code=409,
                            detail=f"이미 처리된 요청입니다 (상태: {ap.status})")

    if body.decision == "approve":
        ap.result = run_tool(ap.tool_name, ap.arguments)   # 승인 시점에 실제 실행
        ap.status = "approved"
    elif body.decision == "reject":
        ap.status = "rejected"
    else:
        raise HTTPException(status_code=400,
                            detail="decision 은 approve 또는 reject 여야 합니다")

    ap.decided_at = _now()
    ap.decided_by = body.admin_id
    db.add(ap)
    db.commit()
    db.refresh(ap)
    return ap