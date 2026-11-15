"""
Small date helpers shared by the transactions list and the summary.

We filter by date RANGES (start <= date < end) instead of database-specific
functions like EXTRACT/strftime, so the same code works on SQLite and PostgreSQL.
"""
from datetime import date

from fastapi import HTTPException


def month_range(month: str) -> tuple[date, date]:
    """'2026-11' -> (2026-11-01, 2026-12-01)"""
    try:
        year, mon = (int(p) for p in month.split("-"))
        start = date(year, mon, 1)
    except ValueError:
        raise HTTPException(status_code=422, detail="month must be YYYY-MM")
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    return start, end
