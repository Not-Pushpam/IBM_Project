"""
Expense dataclass — represents a single expense entry.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date

from financial_assistant.constants import ExpenseCategory


@dataclass
class Expense:
    """Represents one expense entered by the student."""

    category: ExpenseCategory
    description: str
    amount: float
    date: date
    expense_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        """Serialise to a plain dict (used for CSV / JSON persistence)."""
        return {
            "expense_id": self.expense_id,
            "category": self.category.value,
            "description": self.description,
            "amount": self.amount,
            "date": self.date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Expense:
        """Deserialise from a plain dict (used when reading CSV / JSON)."""
        return cls(
            expense_id=data["expense_id"],
            category=ExpenseCategory(data["category"]),
            description=data["description"],
            amount=float(data["amount"]),
            date=date.fromisoformat(data["date"]),
        )
