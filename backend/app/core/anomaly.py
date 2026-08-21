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
