"""
GET /summary — total income, total expense and balance for a period.

Period options (pick one, or none for all-time):
  ?month=2026-11
  ?start_date=2026-11-01&end_date=2026-11-30   (both inclusive)

The totals are computed by the database in ONE query (SUM + CASE), instead of
loading every row into Python — that keeps it fast as data grows.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.filters import month_range
from app.models import Transaction, TransactionType, User
from app.schemas import SummaryOut

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("", response_model=SummaryOut)
def get_summary(
    month: Optional[str] = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if month and (start_date or end_date):
        raise HTTPException(422, "Use either month OR start_date/end_date, not both.")
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, "start_date must be on or before end_date.")

    q = db.query(
        func.coalesce(
            func.sum(case((Transaction.type == TransactionType.income, Transaction.amount), else_=0)), 0
        ),
        func.coalesce(
            func.sum(case((Transaction.type == TransactionType.expense, Transaction.amount), else_=0)), 0
        ),
        func.count(Transaction.id),
    ).filter(Transaction.user_id == current_user.id)

    period_start, period_end = start_date, end_date
    if month:
        period_start, exclusive_end = month_range(month)
        period_end = exclusive_end - timedelta(days=1)
    if period_start:
        q = q.filter(Transaction.date >= period_start)
    if period_end:
        q = q.filter(Transaction.date <= period_end)

    income, expense, count = q.one()
    income = Decimal(str(income)).quantize(Decimal("0.01"))
    expense = Decimal(str(expense)).quantize(Decimal("0.01"))

    return SummaryOut(
        start_date=period_start,
        end_date=period_end,
        total_income=income,
        total_expense=expense,
        balance=income - expense,
        transaction_count=count,
    )
