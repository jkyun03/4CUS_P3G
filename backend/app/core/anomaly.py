"""
사용자의 일별 민감정보 조회 건수를 과거 평균과 비교하는 z-score 기반 이상행동 탐지.
"""
import statistics

MIN_HISTORY_DAYS = 3
Z_THRESHOLD = 2.0


def is_anomalous(today_count: int, historical_daily_counts: list) -> tuple:
    if len(historical_daily_counts) < MIN_HISTORY_DAYS:
        return False, 0.0

    mean = statistics.mean(historical_daily_counts)
    stdev = statistics.pstdev(historical_daily_counts)
    if stdev == 0:
        stdev = 0.5

    z = (today_count - mean) / stdev
    return z >= Z_THRESHOLD, z
