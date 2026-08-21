from app.core.analyzers import RiskSignal


def score(signals: list[RiskSignal]) -> int:
    total = sum(s.score for s in signals)
    return min(total, 100)
