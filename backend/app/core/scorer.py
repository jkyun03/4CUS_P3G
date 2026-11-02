"""
위험 신호 점수를 합산한다(최대 100).
"""
from app.core.analyzers import RiskSignal


def score(signals: list[RiskSignal]) -> int:
    total = sum(s.score for s in signals)
    return min(total, 100)
