from __future__ import annotations
from datetime import datetime, date, time as dt_time, timezone, timedelta
from typing import Optional, Union


def local_now() -> datetime:
    return datetime.now(timezone(timedelta(hours=3)))


def format_dt(dt: Optional[datetime], fmt: str = "%d.%m.%Y %H:%M") -> str:
    if dt is None:
        return ""
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt.strftime(fmt)

    if dt.tzinfo is None:
        dt = dt.replace()

    return dt.strftime(fmt)


def try_parse_datetime(
        date_text: str,
        prefer_date: bool = False
) -> Optional[Union[datetime, date]]:
    if not date_text or not isinstance(date_text, str):
        return None

    s = date_text.strip()
    fmts = ("%d.%m.%Y %H:%M", "%d.%m.%Y")

    for fmt in fmts:
        try:
            parsed = datetime.strptime(s, fmt)

            if fmt == "%d.%m.%Y":
                if prefer_date:
                    return parsed.date()
                parsed = parsed.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

            return parsed.replace()
        except ValueError:
            continue

    try:
        parsed = datetime.fromisoformat(s)

        if isinstance(parsed, date) and not isinstance(parsed, datetime):
            if prefer_date:
                return parsed
            parsed = datetime.combine(parsed, dt_time.min)

        if parsed.tzinfo is None:
            parsed = parsed.replace()

        return parsed
    except Exception:
        return None
