"""
SpendingAnalyzer — category totals and plain-English spending observations.
"""

from __future__ import annotations

from financial_assistant.constants import ExpenseCategory, HIGH_SPEND_THRESHOLD
from financial_assistant.exceptions import BudgetNotSetError, EmptyExpenseListError
from financial_assistant.models.expense import Expense
from financial_assistant.storage.expense_repository import ExpenseRepository


class SpendingAnalyzer:
    """
    Analyses expense data and produces human-readable observations.

    Responsibilities
    ----------------
    * Aggregate spending per category.
    * Identify the highest-spending category.
    * Detect whether any single category exceeds a threshold.
    * Generate a list of plain-English spending observations.

    Parameters
    ----------
    repository : ExpenseRepository
        Shared data store injected from the outside.
    """

    def __init__(self, repository: ExpenseRepository) -> None:
        self._repo = repository

    # ------------------------------------------------------------------
    # Category aggregation
    # ------------------------------------------------------------------

    def get_category_totals(self) -> dict[str, float]:
        """
        Return a dict mapping category name → total amount spent.

        Raises
        ------
        EmptyExpenseListError
            If no expenses have been recorded.
        """
        expenses = self._repo.get_expenses()
        if not expenses:
            raise EmptyExpenseListError("No expenses have been added yet.")

        totals: dict[str, float] = {cat.value: 0.0 for cat in ExpenseCategory}
        for expense in expenses:
            totals[expense.category.value] += expense.amount

        # Remove categories with zero spend so callers get a clean dict
        return {k: v for k, v in totals.items() if v > 0}

    def get_highest_spending_category(self) -> str:
        """Return the category name with the highest total spend."""
        totals = self.get_category_totals()
        return max(totals, key=lambda k: totals[k])

    def is_category_over_threshold(self, category: str, budget: float) -> bool:
        """
        Return True if the named category's total exceeds
        HIGH_SPEND_THRESHOLD (50 %) of the given budget.
        """
        totals = self.get_category_totals()
        return totals.get(category, 0.0) > budget * HIGH_SPEND_THRESHOLD

    # ------------------------------------------------------------------
    # Observations
    # ------------------------------------------------------------------

    def get_spending_patterns(self) -> list[str]:
        """
        Return a list of plain-English observations about the student's spending.

        Raises
        ------
        BudgetNotSetError
            If no budget profile exists.
        EmptyExpenseListError
            If no expenses have been recorded.
        """
        profile = self._repo.get_profile()
        if profile is None:
            raise BudgetNotSetError(
                "Please set your budget before viewing spending analysis."
            )

        expenses = self._repo.get_expenses()
        if not expenses:
            raise EmptyExpenseListError(
                "Add some expenses first to see your spending patterns."
            )

        total_spent = sum(e.amount for e in expenses)
        budget = profile.monthly_budget
        remaining = budget - total_spent
        pct = (total_spent / budget * 100) if budget > 0 else 0
        sym = profile.currency_symbol

        observations: list[str] = []

        # Overall budget usage
        observations.append(
            f"You have spent **{sym}{total_spent:,.2f}** "
            f"({pct:.1f}% of your {sym}{budget:,.2f} budget)."
        )

        if remaining >= 0:
            observations.append(
                f"You have **{sym}{remaining:,.2f}** remaining for this month."
            )
        else:
            observations.append(
                f"⚠️ You are **over budget by {sym}{abs(remaining):,.2f}**."
            )

        # Highest spending category
        totals = self.get_category_totals()
        top_cat = max(totals, key=lambda k: totals[k])
        observations.append(
            f"Your highest spending category is **{top_cat}** "
            f"({sym}{totals[top_cat]:,.2f})."
        )

        # Flag any category that takes more than 50% of budget
        for cat, amount in totals.items():
            if amount > budget * HIGH_SPEND_THRESHOLD:
                observations.append(
                    f"⚠️ **{cat}** spending ({sym}{amount:,.2f}) exceeds 50% of "
                    f"your budget — consider reviewing this."
                )

        # Positive reinforcement
        if remaining > budget * 0.30:
            observations.append(
                "✅ Great job! You still have more than 30% of your budget left."
            )

        return observations
