"""
게이트웨이의 심장: POST /v1/tool_call

에이전트는 도구를 직접 실행하지 않고 이 엔드포인트를 호출한다.
여기서 아래 순서(요청 생명주기)대로 처리한다.
  1. 세션 확인/생성
  2. 호출 기록
  3. 세션 맥락(이전 호출들) 로드   ← 세션 기반 기억의 기초
  4. 툴 별 권한 검사              ← 1순위 기능
  5. 분석 -> 점수 -> 정책 결정
  6. 판정에 따라: 허용/마스킹은 실행(담당 환자 여부까지 반영), 승인은 대기 큐, 차단은 거부
  7. 이벤트(감사 로그) 저장 후 응답
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import AgentSession, ToolCall, Event, Tool, Approval
from app.core import analyzers, scorer, policy
from app.core.masking import mask_data
from app.mcp_tools.registry import run_tool, TOOL_FUNCTIONS
from app.api.approval import manager as approval_manager

router = APIRouter()

# 관리자 승인 대기 제한 시간(분). 이 시간이 지나면 자동 거부(expired).
APPROVAL_TIMEOUT_MIN = 5


class ToolCallRequest(BaseModel):
    session_id: str
    user_request: str          # 사용자의 원래 의도
    tool: str                  # 호출할 도구 이름
    arguments: dict = {}       # 도구 인자
    user_role: str = "doctor"  # 호출자 직군 (권한 검사 + 마스킹 등급 결정용)
    user_id: str = ""          # 호출자 개인 식별자 (예: "doctor_kim") — 담당 환자 판단용


@router.post("/v1/tool_call")
async def handle_tool_call(req: ToolCallRequest, db: Session = Depends(get_session)):
    # 1) 세션이 없으면 생성
    sess = db.get(AgentSession, req.session_id)
    if not sess:
        sess = AgentSession(id=req.session_id, user_id=req.user_id or req.user_role,
                            user_request=req.user_request)
        db.add(sess)
        db.commit()

    # 2) 이번 호출을 기록
    call = ToolCall(session_id=req.session_id, tool_name=req.tool,
                    arguments=req.arguments)
    db.add(call)
    db.commit()
    db.refresh(call)

    # 3) 세션 맥락: 이 세션의 '이전' 호출들
    history = db.exec(
        select(ToolCall)
        .where(ToolCall.session_id == req.session_id)
        .where(ToolCall.id < call.id)
    ).all()
    history_names = [c.tool_name for c in history]
    history_calls = [(c.tool_name, c.arguments) for c in history]

    # 4) 툴 별 권한 검사 (여기서 걸리면 분석 없이 즉시 차단)
    tool_row = db.exec(select(Tool).where(Tool.name == req.tool)).first()
    permission_reason = None
    if tool_row is None:
        permission_reason = f"등록되지 않은 도구: {req.tool}"
    elif not tool_row.enabled:
        permission_reason = f"비활성화된 도구: {req.tool}"
    elif tool_row.allowed_roles and req.user_role not in tool_row.allowed_roles:
        permission_reason = f"권한 없음: '{req.user_role}' 역할은 {req.tool} 호출 불가"

    if permission_reason:
        event = _save_event(db, call, req, 100, "block", [permission_reason], False)
        return _response(event, None)

    # 5) 분석 -> 점수 -> 정책
    signals = analyzers.analyze(req.tool, req.arguments, req.user_request,
                                history_names, history_calls=history_calls)
    risk = scorer.score(signals)
    decision = policy.decide(risk, signals, req.tool)

    # 6) 판정에 따라 처리
    result = None
    approval_id = None

    if decision.action in ("allow", "warn", "mask"):
        # 허용/경고/마스킹 -> 도구 실행 (마스킹은 직군·담당 환자 여부까지 반영)
        result = await run_tool(req.tool, req.arguments)
        if req.tool in TOOL_FUNCTIONS:   # 병원 mock 도구일 때만 필드명 기반 마스킹 적용
            result = mask_data(result, role=req.user_role, user_id=req.user_id)
        event = _save_event(db, call, req, risk, decision.action,
                            decision.reasons, decision.masked)

    elif decision.action == "approve":
        # 승인 필요 -> 실행하지 말고 대기 큐에 넣는다 (관리자 결정까지 보류)
        event = _save_event(db, call, req, risk, "approve",
                            decision.reasons, decision.masked)
        approval = Approval(
            event_id=event.id,
            session_id=req.session_id,
            tool_name=req.tool,
            arguments=req.arguments,
            risk_score=risk,
            reasons=decision.reasons,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=APPROVAL_TIMEOUT_MIN),
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        approval_id = approval.id

        # 관리자 승인 큐 화면에 실시간으로 알림
        await approval_manager.broadcast({
            "type": "new_approval",
            "approval_id": approval.id,
            "tool": req.tool,
            "risk_score": risk,
        })

    else:  # block
        event = _save_event(db, call, req, risk, "block",
                            decision.reasons, decision.masked)

    return _response(event, result, approval_id)


# ---- 내부 도우미 함수 --------------------------------------------------
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
        "event_id": event.id,
        "decision": event.decision,
        "risk_score": event.risk_score,
        "reasons": event.reasons,
        "masked": event.masked,
        "result": result,
        "approval_id": approval_id,   # 승인 대기일 때만 값이 있음. 이 id로 상태를 조회한다.
    }