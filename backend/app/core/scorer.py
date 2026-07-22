"""
위험 점수 계산기.

분석기가 만든 신호들의 점수를 합산한다. 최대 100점으로 자른다.
"""
from app.core.analyzers import RiskSignal


def score(signals: list[RiskSignal]) -> int:
    total = sum(s.score for s in signals)
    return min(total, 100)
