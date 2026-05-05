from datetime import datetime, date, timezone, timedelta

UTC_PLUS_8 = timezone(timedelta(hours=8))


def now() -> datetime:
    """当前 UTC+8 时间。"""
    return datetime.now(UTC_PLUS_8)


def now_iso() -> str:
    """当前 UTC+8 时间的 ISO 格式字符串（SQLite 兼容）。"""
    return now().strftime("%Y-%m-%d %H:%M:%S")


def today() -> date:
    """当前 UTC+8 日期。"""
    return now().date()


def today_iso() -> str:
    """当前 UTC+8 日期 ISO 格式字符串。"""
    return today().isoformat()


def format_date(d: date) -> str:
    """日期 -> ISO 字符串。"""
    return d.isoformat()
