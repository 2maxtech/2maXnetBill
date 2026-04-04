import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ExpenseCategory(str, enum.Enum):
    electricity = "electricity"
    internet = "internet"
    salary = "salary"
    equipment = "equipment"
    maintenance = "maintenance"
    rent = "rent"
    other = "other"


class Expense(BaseModel):
    __tablename__ = "expenses"

    category: Mapped[ExpenseCategory] = mapped_column(Enum(ExpenseCategory), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
