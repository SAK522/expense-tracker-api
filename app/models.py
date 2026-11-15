"""
Database tables, described as Python classes (SQLAlchemy ORM).

Two tables:
- users:        who can log in
- transactions: each income/expense row, always linked to one user via user_id
"""
from datetime import datetime, timezone
import enum

from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Numeric, ForeignKey, Enum,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    # Deleting a user deletes their transactions too.
    transactions = relationship(
        "Transaction", back_populates="owner", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    # The ownership link. Every query filters on this column, which is what
    # keeps one user's data invisible to another.
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # Numeric (not Float) so money never suffers rounding errors.
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(Enum(TransactionType, name="transaction_type"), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    note = Column(String(255), nullable=True)
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    owner = relationship("User", back_populates="transactions")
