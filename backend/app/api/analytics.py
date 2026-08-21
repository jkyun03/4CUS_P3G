from collections import Counter

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import Event, Approval

router = APIRouter()


@router.get("/analytics/summary")
def analytics_summary(db: Session = Depends(get_session)):
    events = db.exec(select(Event)).all()

    by_decision = Counter(e.decision for e in events)
    tool_counts = Counter(e.tool_name for e in events)
    masked_count = sum(1 for e in events if e.masked)
    pending = db.exec(select(Approval).where(Approval.status == "pending")).all()
    top_tools = [{"tool": name, "count": cnt} for name, cnt in tool_counts.most_common(5)]

    return {
        "total_events": len(events),
        "by_decision": dict(by_decision),
        "blocked": by_decision.get("block", 0),
        "masked": masked_count,
        "pending_approvals": len(pending),
        "top_tools": top_tools,
    }