"""
데이터 모델 
"""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AgentSession(SQLModel, table=True):
    id: str = Field(primary_key=True)             
    user_id: str                                  
    user_request: str                             
    created_at: datetime = Field(default_factory=_now)


class ToolCall(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="agentsession.id", index=True)
    user_id: str = Field(index=True, default="")
    tool_name: str
    arguments: dict = Field(default_factory=dict, sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=_now)


class Event(SQLModel, table=True):
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
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    role: str                                     # "진료기록 조회"
    base_risk: str                                # low | medium | high
    enabled: bool = True
    allowed_roles: list = Field(default_factory=list, sa_column=Column(JSON))
    description: str = ""                         
    baseline_description: Optional[str] = None     

class Approval(SQLModel, table=True):
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
    expires_at: datetime                     # 이 시각이 지나면 자동 거부
    
class PolicyThreshold(SQLModel, table=True):
        id: int = Field(default=1, primary_key=True)
        warn: int = 30       # 30점 이상 경고
        approve: int = 60    # 60점 이상 승인 필요
        block: int = 80      # 80점 이상 차단

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    salt: str
    role: str
    user_id: str
    display_name: str = ""