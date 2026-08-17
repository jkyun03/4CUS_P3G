"""
게이트웨이의 심장: POST /v1/tool_call
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import AgentSession, ToolCall, Event, Tool, Approval, PolicyThreshold
from app.core import analyzers, scorer, policy, tool_integrity, prompt_injection
from app.core.masking import mask_data
from app.mcp_tools.registry import run_tool, TOOL_FUNCTIONS
from app.api.approval import manager as approval_manager
from app.api.auth import get_current_user

router = APIRouter()

APPROVAL_TIMEOUT_MIN = 5
RISK_TIME_WINDOW_MIN = 10


class ToolCallRequest(BaseModel):
    session_id: str
    user_request: str
    tool: str
    arguments: dict = {}


@router.post("/v1/tool_call")
async def handle_tool_call(
    req: ToolCallRequest,
    db: Session = Depends(get_session),
    identity: dict = Depends(get_current_user),
):
    user_role = identity["role"]
    user_id = identity["user_id"]

    sess = db.get(AgentSession, req.session_id)
    if not sess:
        sess = AgentSession(id=req.session_id, user_id=user_id, user_request=req.user_request)
        db.add(sess)
        db.commit()

    call = ToolCall(session_id=req.session_id, user_id=user_id,
                    tool_name=req.tool, arguments=req.arguments)
    db.add(call)
    db.commit()
    db.refresh(call)

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=RISK_TIME_WINDOW_MIN)
    recent = db.exec(
        select(ToolCall)
        .where(ToolCall.user_id == user_id)
        .where(ToolCall.timestamp >= cutoff)
        .where(ToolCall.id < call.id)
    ).all()
    history_names = [c.tool_name for c in recent]
    history_calls = [(c.tool_name, c.arguments) for c in recent]

    tool_row = db.exec(select(Tool).where(Tool.name == req.tool)).first()
    permission_reason = None
    if tool_row is None:
        permission_reason = f"등록되지 않은 도구: {req.tool}"
    elif not tool_row.enabled:
        permission_reason = f"비활성화된 도구: {req.tool}"
    elif tool_row.allowed_roles and user_role not in tool_row.allowed_roles:
        permission_reason = f"권한 없음: '{user_role}' 역할은 {req.tool} 호출 불가"
    else:
        if tool_integrity.scan_description(tool_row.description):
            permission_reason = f"도구 설명에 숨겨진 지시문 의심 패턴 포함: {req.tool}"
        else:
            tamper_reason, current_hash = tool_integrity.check_tampering(
                tool_row.name, tool_row.description, tool_row.signature_hash)
            if tamper_reason:
                permission_reason = tamper_reason
            elif tool_row.signature_hash is None:
                tool_row.signature_hash = current_hash
                db.add(tool_row)
                db.commit()

    if permission_reason:
        event = _save_event(db, call, req, 100, "block", [permission_reason], False)
        return _response(event, None)

    signals = analyzers.analyze(req.tool, req.arguments, req.user_request,
                                history_names, history_calls=history_calls)
    risk = scorer.score(signals)
    th = db.get(PolicyThreshold, 1)
    thresholds = policy.Thresholds(warn=th.warn, approve=th.approve, block=th.block) if th else None
    decision = policy.decide(risk, signals, req.tool, thresholds)

    result = None
    approval_id = None

    if decision.action in ("allow", "warn", "mask"):
        result = await run_tool(req.tool, req.arguments)

        reasons = list(decision.reasons)
        audit_risk = risk
        injection_hits = prompt_injection.scan_value(result)
        if injection_hits:
            result = prompt_injection.redact(result)
            reasons.append(f"도구 실행 결과에서 프롬프트 인젝션 의심 패턴 탐지·제거 ({len(injection_hits)}건)")
            audit_risk = min(risk + 45, 100)

        if req.tool in TOOL_FUNCTIONS:
            result = mask_data(result, role=user_role, user_id=user_id)
        event = _save_event(db, call, req, audit_risk, decision.action, reasons, decision.masked)

    elif decision.action == "approve":
        event = _save_event(db, call, req, risk, "approve", decision.reasons, decision.masked)
        approval = Approval(
            event_id=event.id, session_id=req.session_id, tool_name=req.tool,
            arguments=req.arguments, risk_score=risk, reasons=decision.reasons,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=APPROVAL_TIMEOUT_MIN),
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        approval_id = approval.id

        await approval_manager.broadcast({
            "type": "new_approval", "approval_id": approval.id,
            "tool": req.tool, "risk_score": risk,
        })

    else:
        event = _save_event(db, call, req, risk, "block", decision.reasons, decision.masked)

    return _response(event, result, approval_id)


def _save_event(db, call, req, risk, action, reasons, masked) -> Event:
    event = Event(
        tool_call_id=call.id, session_id=req.session_id, tool_name=req.tool,
        risk_score=risk, decision=action, reasons=reasons, masked=masked,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _response(event: Event, result, approval_id=None):
    return {
        "event_id": event.id, "decision": event.decision, "risk_score": event.risk_score,
        "reasons": event.reasons, "masked": event.masked, "result": result,
        "approval_id": approval_id,
    }