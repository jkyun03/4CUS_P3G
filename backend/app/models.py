"""
데이터 모델 

table=True 를 붙인 클래스 하나가 DB 테이블 하나가 된다.
JSON 컬럼에는 dict/list 를 통째로 저장할 수 있다.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON


def _now() -> datetime:
    """현재 시각(UTC). 기본 timestamp 값으로 사용."""
    return datetime.now(timezone.utc)


class AgentSession(SQLModel, table=True):
    """대화 세션 하나. user_request = 사용자가 원래 요청한 '의도'."""
    id: str = Field(primary_key=True)             
    user_id: str                                  
    user_request: str                             
    created_at: datetime = Field(default_factory=_now)


class ToolCall(SQLModel, table=True):
    """에이전트가 호출한 도구 한 건의 원본 기록."""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="agentsession.id", index=True)
    user_id: str = Field(index=True, default="")
    tool_name: str
    arguments: dict = Field(default_factory=dict, sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=_now)


class Event(SQLModel, table=True):
    """판정 결과. 이 테이블이 곧 '감사 로그'의 실체다."""
    id: Optional[int] = Field(default=None, primary_key=True)
    tool_call_id: int = Field(foreign_key="toolcall.id")
    session_id: str = Field(index=True)
    tool_name: str
    risk_score: int
    decision: str                                 # allow | mask | warn | approve | block
    reasons: list = Field(default_factory=list, sa_column=Column(JSON))
    masked: bool = False
    created_at: datetime = Field(default_factory=_now, index=True)


class Tool(SQLModel, table=True):
    """
    도구 정의 + 권한
    enabled: 도구를 켜고 끄기 가능
    allowed_roles: 이 도구를 호출할 수 있는 사용자 역할 목록
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    role: str                                     # "진료기록 조회"
    base_risk: str                                # low | medium | high
    enabled: bool = True
    allowed_roles: list = Field(default_factory=list, sa_column=Column(JSON))
    description: str = ""                         
    baseline_description: Optional[str] = None     

class Approval(SQLModel, table=True):
    """
    관리자 승인 대기 건. (=> '관리자 승인' 기능의 데이터 기반)
    위험 점수가 승인 구간(60~79)이면 도구를 바로 실행하지 않고
    이 표에 pending 으로 넣어 두고, 관리자가 승인/거부할 때까지 기다린다.
    나중에 실행에 필요하므로 tool_name/arguments 도 함께 저장한다.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    session_id: str = Field(index=True)
    tool_name: str
    arguments: dict = Field(default_factory=dict, sa_column=Column(JSON))
    risk_score: int
    reasons: list = Field(default_factory=list, sa_column=Column(JSON))
    status: str = "pending"                  # pending | approved | rejected | expired
    result: Optional[dict] = Field(default=None, sa_column=Column(JSON))  # 승인 후 실행 결과
    requested_at: datetime = Field(default_factory=_now)
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    expires_at: datetime                     # 이 시각이 지나면 자동 거부(expired)
    
class PolicyThreshold(SQLModel, table=True):
        id: int = Field(default=1, primary_key=True)
        warn: int = 30       # 30점 이상 경고
        approve: int = 60    # 60점 이상 승인 필요
        block: int = 80      # 80점 이상 차단

class User(SQLModel, table=True):
    """로그인 계정."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    salt: str
    role: str
    user_id: str
    display_name: str = ""