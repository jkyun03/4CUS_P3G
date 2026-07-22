"""
게이트웨이의 심장: POST /v1/tool_call

에이전트는 도구를 직접 실행하지 않고 이 엔드포인트를 호출한다.
여기서 아래 순서(요청 생명주기)대로 처리한다.
  1. 세션 확인/생성
  2. 호출 기록
  3. 세션 맥락(이전 호출들) 로드   ← 세션 기반 기억의 기초
  4. 툴 별 권한 검사              ← 1순위 기능
  5. 분석 -> 점수 -> 정책 결정
  6. 허용이면 도구 실행(마스킹이면 결과를 가림), 차단/승인이면 실행 안 함
  7. 이벤트(감사 로그) 저장 후 응답
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import AgentSession, ToolCall, Event, Tool
from app.core import analyzers, scorer, policy
from app.core.masking import mask_data
from app.mcp_tools.registry import run_tool

router = APIRouter()


class ToolCallRequest(BaseModel):
    session_id: str
    user_request: str          # 사용자의 원래 의도
    tool: str                  # 호출할 도구 이름
    arguments: dict = {}       # 도구 인자
    user_role: str = "doctor"  # 호출자 역할 (권한 검사용)


@router.post("/v1/tool_call")
def handle_tool_call(req: ToolCallRequest, db: Session = Depends(get_session)):
    # 1) 세션이 없으면 생성
    sess = db.get(AgentSession, req.session_id)
    if not sess:
        sess = AgentSession(id=req.session_id, user_id=req.user_role,
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
    signals = analyzers.analyze(req.tool, req.arguments, req.user_request, history_names)
    risk = scorer.score(signals)
    decision = policy.decide(risk, signals, req.tool)

    # 6) 실행 (허용/경고/마스킹일 때만)
    result = None
    if decision.action in ("allow", "warn", "mask"):
        result = run_tool(req.tool, req.arguments)
        if decision.action == "mask":
            result = mask_data(result)

    # 7) 이벤트 저장 + 응답
    event = _save_event(db, call, req, risk, decision.action,
                        decision.reasons, decision.masked)
    return _response(event, result)


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


def _response(event: Event, result):
    return {
        "event_id": event.id,
        "decision": event.decision,
        "risk_score": event.risk_score,
        "reasons": event.reasons,
        "masked": event.masked,
        "result": result,
    }
