FREQUENCY_MAPPING = {
    "1h": {"candleType": "minute", "candleDuration": 1, "limit": 60},
    "4h": {"candleType": "minute", "candleDuration": 1, "limit": 240},
    "1d": {"candleType": "minute", "candleDuration": 5, "limit": 288},
    "1w": {"candleType": "hour", "candleDuration": 1, "limit": 168},
    "1m": {"candleType": "hour", "candleDuration": 4, "limit": 186},
    "all": {"candleType": "hour", "candleDuration": 12, "limit": 300},
}

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY
MONTH = 30 * DAY

DURATION_MAPPING = {
    "1h": HOUR,
    "4h": 4 * HOUR,
    "1d": DAY,
    "1w": WEEK,
    "1m": MONTH,
    "all": None
}
