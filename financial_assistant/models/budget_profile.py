"""
BudgetProfile dataclass — holds the student's monthly income and budget.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BudgetProfile:
    """Stores the student's declared monthly income, planned budget and currency."""

    monthly_income: float
    monthly_budget: float
    currency_symbol: str = "$"

    def to_dict(self) -> dict:
        return {
            "monthly_income": self.monthly_income,
            "monthly_budget": self.monthly_budget,
            "currency_symbol": self.currency_symbol,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BudgetProfile:
        return cls(
            monthly_income=float(data["monthly_income"]),
            monthly_budget=float(data["monthly_budget"]),
            currency_symbol=data.get("currency_symbol", "$"),
        )
