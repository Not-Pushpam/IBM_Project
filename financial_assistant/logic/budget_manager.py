"""
BudgetManager — handles income/budget setup and remaining-budget calculations.
"""

from __future__ import annotations

from financial_assistant.exceptions import BudgetNotSetError, InvalidAmountError
from financial_assistant.models.budget_profile import BudgetProfile
from financial_assistant.storage.expense_repository import ExpenseRepository


class BudgetManager:
    """
    Manages the student's monthly income and budget.

    Responsibilities
    ----------------
    * Validate and store monthly income and budget.
    * Calculate remaining budget given total spending.
    * Determine whether the student is over budget.

    Parameters
    ----------
    repository : ExpenseRepository
        Shared data store injected from the outside (easy to mock in tests).
    """

    def __init__(self, repository: ExpenseRepository) -> None:
        self._repo = repository

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def set_profile(
        self,
        monthly_income: float,
        monthly_budget: float,
        currency_symbol: str = "$",
    ) -> BudgetProfile:
        """
        Validate and save the student's monthly income and budget.

        Returns
        -------
        BudgetProfile
            The saved profile.

        Raises
        ------
        InvalidAmountError
            If income < 0 or budget <= 0.
        """
        if monthly_income < 0:
            raise InvalidAmountError("Monthly income cannot be negative.")
        if monthly_budget <= 0:
            raise InvalidAmountError("Monthly budget must be greater than zero.")

        profile = BudgetProfile(
            monthly_income=monthly_income,
            monthly_budget=monthly_budget,
            currency_symbol=currency_symbol,
        )
        self._repo.save_profile(profile)
        return profile

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_profile(self) -> BudgetProfile:
        """
        Return the current budget profile.

        Raises
        ------
        BudgetNotSetError
            If no profile has been saved yet.
        """
        profile = self._repo.get_profile()
        if profile is None:
            raise BudgetNotSetError(
                "No budget has been set yet. Please enter your income and budget first."
            )
        return profile

    def get_remaining_budget(self, total_spent: float) -> float:
        """Return budget minus total_spent (may be negative if over budget)."""
        profile = self.get_profile()
        return profile.monthly_budget - total_spent

    def is_over_budget(self, total_spent: float) -> bool:
        """Return True when total_spent exceeds the monthly budget."""
        return total_spent > self.get_profile().monthly_budget

    def budget_exceeds_income(self) -> bool:
        """Return True when the budget is larger than declared income."""
        profile = self.get_profile()
        return profile.monthly_budget > profile.monthly_income
