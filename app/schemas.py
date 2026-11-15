"""
Pydantic schemas = the shape of data crossing the API boundary.
Input schemas validate what clients send; output schemas control exactly
what we send back (e.g. UserOut never contains a password field).
"""
from datetime import date as dt_date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import TransactionType


# ---------- Users / auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Transactions ----------

class TransactionBase(BaseModel):
    # gt=0: amounts are always positive; `type` says whether it's in or out.
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    type: TransactionType
    category: str = Field(min_length=1, max_length=50)
    note: Optional[str] = Field(default=None, max_length=255)
    date: dt_date


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    """All fields optional: send only what you want to change."""
    amount: Optional[Decimal] = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    type: Optional[TransactionType] = None
    category: Optional[str] = Field(default=None, min_length=1, max_length=50)
    note: Optional[str] = Field(default=None, max_length=255)
    date: Optional[dt_date] = None


class TransactionOut(TransactionBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Summary ----------

class SummaryOut(BaseModel):
    start_date: Optional[dt_date]
    end_date: Optional[dt_date]
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    transaction_count: int
