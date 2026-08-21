from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import Event, ToolCall, AgentSession

router = APIRouter()


@router.get("/events")
def list_events(limit: int = 50, db: Session = Depends(get_session)):
    events = db.exec(select(Event).order_by(Event.id.desc()).limit(limit)).all()
    return [
        {
            "event_id": e.id, "session_id": e.session_id, "tool_name": e.tool_name,
            "risk_score": e.risk_score, "decision": e.decision, "reasons": e.reasons,
            "masked": e.masked,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.get("/events/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_session)):
    e = db.get(Event, event_id)
    if not e:
        raise HTTPException(status_code=404, detail="이벤트를 찾을 수 없음")
    calls = db.exec(
        select(ToolCall).where(ToolCall.session_id == e.session_id).order_by(ToolCall.id)
    ).all()
    sess = db.get(AgentSession, e.session_id)
    return {
        "event_id": e.id, "session_id": e.session_id,
        "user_request": sess.user_request if sess else "",
        "tool_name": e.tool_name, "risk_score": e.risk_score, "decision": e.decision,
        "reasons": e.reasons, "masked": e.masked,
        "flow": [c.tool_name for c in calls],
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }