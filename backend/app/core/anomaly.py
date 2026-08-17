"""
사용자별 행동 이상탐지 (behavioral anomaly detection).

'세션 안에서 3번 이상 조회하면 위험'처럼 고정된 임계값 대신, 이 사용자의 평소 패턴
(최근 N일간 하루 평균 민감정보 조회 건수) 대비 오늘 얼마나 벗어났는지를 통계적으로
판단한다. 평소 하루 2건 보던 사람이 갑자기 15건을 보면, 고정 임계값보다 훨씬 더
직관적으로 "평소와 다르다"는 신호를 잡아낼 수 있다.

이 파일은 DB에 의존하지 않는 순수 파이썬이다 — 날짜별 건수 리스트만 받아서 판단하고,
DB 조회는 호출하는 쪽(app/api/tool_call.py)에서 한다.
"""
import statistics

MIN_HISTORY_DAYS = 3   # 이 정도는 쌓여야 '평소 패턴'이라고 할 수 있다 (데이터 부족 시 판단 보류)
Z_THRESHOLD = 2.0       # 표준편차의 몇 배 이상 벗어나면 이상치로 볼지


def is_anomalous(today_count: int, historical_daily_counts: list) -> tuple:
    """
    반환: (이상치 여부, z-score)
    historical_daily_counts: 오늘을 제외한 최근 N일간의 일별 건수 리스트.
    """
    if len(historical_daily_counts) < MIN_HISTORY_DAYS:
        return False, 0.0  # 데이터 부족 -> 판단 보류(오탐 방지)

    mean = statistics.mean(historical_daily_counts)
    stdev = statistics.pstdev(historical_daily_counts)
    if stdev == 0:
        stdev = 0.5  # 항상 똑같은 건수였다면, 작은 변화도 이상치로 안 보이도록 최소값 사용

    z = (today_count - mean) / stdev
    return z >= Z_THRESHOLD, z
