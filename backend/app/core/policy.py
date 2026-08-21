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
    t = thresholds or Thresholds()
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