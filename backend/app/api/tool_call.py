"""
게이트웨이의 심장: POST /v1/tool_call
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import AgentSession, ToolCall, Event, Tool, Approval, PolicyThreshold
from app.core import analyzers, scorer, policy, tool_integrity, prompt_injection, ml_classifier, anomaly
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
        # 4-1) 툴 포이즈닝 검사: 설명에 숨은 지시문 + 최초 등록 이후 의미적 변조(rug-pull) 여부
        if tool_integrity.scan_description(tool_row.description):
            permission_reason = f"도구 설명에 숨겨진 지시문 의심 패턴 포함: {req.tool}"
        else:
            tamper_reason, new_baseline = tool_integrity.check_tampering(
                tool_row.name, tool_row.description, tool_row.baseline_description)
            if tamper_reason:
                permission_reason = tamper_reason
            elif new_baseline != tool_row.baseline_description:
                tool_row.baseline_description = new_baseline
                db.add(tool_row)
                db.commit()

    if permission_reason:
        event = _save_event(db, call, req, 100, "block", [permission_reason], False)
        return _response(event, None)

    signals = analyzers.analyze(req.tool, req.arguments, req.user_request,
                                history_names, history_calls=history_calls)

    # 5-1) 사용자별 행동 이상탐지: 오늘 이 사용자의 민감정보 조회 건수가 평소 패턴을 벗어났는가
    if req.tool in analyzers.SENSITIVE_READ_TOOLS:
        user_key = user_id or user_role
        daily_counts = _daily_sensitive_counts(db, user_key, analyzers.SENSITIVE_READ_TOOLS)
        today_key = datetime.now(timezone.utc).date().isoformat()
        today_count = daily_counts.pop(today_key, 0)  # 이번 호출은 2)에서 이미 기록됨
        anomalous, z = anomaly.is_anomalous(today_count, list(daily_counts.values()))
        if anomalous:
            signals.append(analyzers.RiskSignal(
                "behavior_anomaly", 30,
                f"평소 패턴 대비 이상 행동: 오늘 민감정보 {today_count}건 조회 (z-score {z:.1f})"))

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
        is_ml_flagged, ml_confidence = ml_classifier.predict(str(result))
        if is_ml_flagged:
            injection_hits.append(f"ML 분류기 의심 (확률 {ml_confidence:.0%})")
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


# ---- 내부 도우미 함수 --------------------------------------------------
def _daily_sensitive_counts(db, user_id: str, tool_names, lookback_days: int = 14) -> dict:
    """이 user_id가 최근 N일간 민감 도구를 하루에 몇 번씩 호출했는지(날짜별 건수)."""
    rows = db.exec(
        select(ToolCall.timestamp)
        .where(ToolCall.user_id == user_id)
        .where(ToolCall.tool_name.in_(list(tool_names)))
    ).all()
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    by_day = defaultdict(int)
    for ts in rows:
        if ts.tzinfo is None:  # SQLite에서 읽은 시각엔 시간대 정보가 없을 수 있다
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= cutoff:
            by_day[ts.date().isoformat()] += 1
    return by_day


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