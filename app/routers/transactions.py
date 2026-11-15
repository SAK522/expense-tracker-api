"""
Transaction routes — all protected by the JWT guard.

Ownership rule: every query is scoped with `Transaction.user_id == current_user.id`.
If a user asks for someone else's transaction id, we return 404 (not 403),
so we don't even reveal that the id exists.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.filters import month_range
from app.models import Transaction, TransactionType, User
from app.schemas import TransactionCreate, TransactionOut, TransactionUpdate

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _get_owned_or_404(db: Session, tx_id: int, user: User) -> Transaction:
    tx = (
        db.query(Transaction)
        .filter(Transaction.id == tx_id, Transaction.user_id == user.id)
        .first()
    )
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return tx


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # user_id comes from the token, never from the request body.
    tx = Transaction(**payload.model_dump(), user_id=current_user.id)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    month: Optional[str] = Query(
        default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Filter by month, format YYYY-MM (e.g. 2026-11)",
    ),
    category: Optional[str] = Query(default=None, max_length=50),
    type: Optional[TransactionType] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if month:
        start, end = month_range(month)
        q = q.filter(Transaction.date >= start, Transaction.date < end)
    if category:
        q = q.filter(Transaction.category.ilike(category))
    if type:
        q = q.filter(Transaction.type == type)

    return (
        q.order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{tx_id}", response_model=TransactionOut)
def get_transaction(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_owned_or_404(db, tx_id, current_user)


@router.put("/{tx_id}", response_model=TransactionOut)
def update_transaction(
    tx_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = _get_owned_or_404(db, tx_id, current_user)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is None and field != "note":
            raise HTTPException(status_code=422, detail=f"'{field}' cannot be null.")
        setattr(tx, field, value)
    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = _get_owned_or_404(db, tx_id, current_user)
    db.delete(tx)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
