"""
정책 엔진.

위험 점수를 보고 어떤 조치를 할지 결정한다.
  0~29  허용(allow)
  30~59 경고(warn)
  60~79 관리자 승인 필요(approve)
  80+   차단(block)

추가 규칙(데이터 최소화):
  차단/승인 대상이 아닌 '민감정보 조회'는 기본적으로 마스킹(mask)해서 돌려준다.
  => 완전히 막지 않고, 필요한 만큼만 보여준다.
  (담당자 서희가 화이트리스트 기반으로 더 정교하게 확장 예정)
"""
from dataclasses import dataclass

from app.core.analyzers import RiskSignal, SENSITIVE_READ_TOOLS


@dataclass
class Decision:
    action: str          # allow | mask | warn | approve | block
    masked: bool
    reasons: list[str]


def decide(score_value: int, signals: list[RiskSignal], tool_name: str) -> Decision:
    if score_value >= 80:
        action = "block"
    elif score_value >= 60:
        action = "approve"
    elif score_value >= 30:
        action = "warn"
    else:
        action = "allow"

    masked = False
    # 허용/경고 수준의 민감정보 조회 -> 마스킹으로 승격
    if action in ("allow", "warn") and tool_name in SENSITIVE_READ_TOOLS:
        action = "mask"
        masked = True

    return Decision(action=action, masked=masked,
                    reasons=[s.reason for s in signals])
