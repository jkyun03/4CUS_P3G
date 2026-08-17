"""
정책 엔진.

위험 점수를 보고 어떤 조치를 할지 결정한다. 임계값(warn/approve/block)은
DB(PolicyThreshold)에서 로드해 /rules API로 조정 가능하다 (기본값 30/60/80).

추가 규칙(데이터 최소화):
  차단/승인 대상이 아닌 '민감정보 조회'는 기본적으로 마스킹(mask)해서 돌려준다.
  => 완전히 막지 않고, 필요한 만큼만 보여준다.
"""
from dataclasses import dataclass

from app.core.analyzers import RiskSignal, SENSITIVE_READ_TOOLS

@dataclass
class Thresholds:
    warn: int = 30
    approve: int = 60
    block: int = 80

@dataclass
class Decision:
    action: str
    masked: bool
    reasons: list

def decide(score_value, signals, tool_name, thresholds=None):
    t = thresholds or Thresholds()   # 안 주면 기본값 사용
    if score_value >= t.block:
        action = "block"
    elif score_value >= t.approve:
        action = "approve"
    elif score_value >= t.warn:
        action = "warn"
    else:
        action = "allow"
    masked = False
    if action in ("allow", "warn") and tool_name in SENSITIVE_READ_TOOLS:
        action = "mask"; masked = True
    return Decision(action=action, masked=masked, reasons=[s.reason for s in signals])