from datetime import datetime, timedelta, timezone


def get_now_timestamp():
    """
    returns 10 digits timestamp
    """
    return int(datetime.now(timezone.utc).timestamp())


def get_now_string_date(format: str = "%Y-%m-%d"):
    """
    returns date in string format
    """
    return datetime.now(timezone.utc).strftime(format)


def convert_timestamp_to_string(timestamp: int, _format: str = "%d %B %Y") -> str:
    return datetime.fromtimestamp(timestamp).strftime(_format)


def convert_string_to_datetime(date: str, _format: str = "%Y-%m-%dT%H:%M:%S"):
    return datetime.strptime(date, _format)


def convert_string_to_timestamp(date: str, _format: str = "%Y-%m-%dT%H:%M:%S"):
    date = convert_string_to_datetime(date, _format)
    return convert_date_to_timestamp(date)


def add_time_to_datetime(date: datetime = None, seconds: int = 0) -> datetime:
    date = datetime.now() if not date else date
    return date + timedelta(seconds=seconds)


def convert_date_to_timestamp(date: datetime = None) -> int:
    date = datetime.now() if not date else date
    return int(date.timestamp())


def convert_date_to_string(date: datetime, _format: str = "%B %d, %Y") -> str:
    if isinstance(date, str):
        date = date.split(" ")[0]
        date = convert_string_to_datetime(date, "%Y-%m-%d")
    
    return date.strftime(_format)


def increase_days_to_timestamp(timestamp: int, days: int) -> int:
    date = datetime.fromtimestamp(timestamp)
    return int((date + timedelta(days=days)).timestamp())


def decrease_days_to_timestamp(timestamp: int, days: int) -> int:
    date = datetime.fromtimestamp(timestamp)
    return int((date - timedelta(days=days)).timestamp())