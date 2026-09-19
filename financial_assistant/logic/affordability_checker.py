"""
AffordabilityChecker — answers the "Can I afford this?" question.
"""

from __future__ import annotations

from financial_assistant.constants import DISCLAIMER
from financial_assistant.exceptions import BudgetNotSetError, InvalidAmountError
from financial_assistant.storage.expense_repository import ExpenseRepository


class AffordabilityChecker:
    """
    Compares an item price against the student's remaining budget.

    Responsibilities
    ----------------
    * Determine whether an item is affordable given the remaining budget.
    * Produce a plain-English explanation of the result.

    Parameters
    ----------
    repository : ExpenseRepository
        Shared data store injected from the outside.
    """

    def __init__(self, repository: ExpenseRepository) -> None:
        self._repo = repository

    # ------------------------------------------------------------------
    # Core check
    # ------------------------------------------------------------------

    def can_afford(self, item_price: float, remaining_budget: float) -> bool:
        """Return True when item_price is within the remaining budget."""
        return item_price <= remaining_budget

    def check(
        self,
        item_name: str,
        item_price: float,
        total_spent: float,
    ) -> tuple[bool, str]:
        """
        Full affordability check using live profile data.

        Parameters
        ----------
        item_name : str
            Name of the item the student wants to buy.
        item_price : float
            Price of the item.
        total_spent : float
            How much the student has already spent this month.

        Returns
        -------
        tuple[bool, str]
            ``(affordable, explanation_message)``

        Raises
        ------
        BudgetNotSetError
            If no budget profile has been set.
        InvalidAmountError
            If item_price <= 0.
        """
        profile = self._repo.get_profile()
        if profile is None:
            raise BudgetNotSetError(
                "Please set your budget before using the affordability checker."
            )

        if item_price <= 0:
            raise InvalidAmountError("Item price must be greater than zero.")

        sym = profile.currency_symbol
        remaining = profile.monthly_budget - total_spent
        affordable = self.can_afford(item_price, remaining)

        if affordable:
            after_purchase = remaining - item_price
            message = (
                f"✅ **Yes, you can afford '{item_name}'!**\n\n"
                f"- Item price: **{sym}{item_price:,.2f}**\n"
                f"- Your remaining budget: **{sym}{remaining:,.2f}**\n"
                f"- Budget remaining *after* purchase: **{sym}{after_purchase:,.2f}**\n\n"
                f"This is a budgeting calculation based on your entered data."
            )
        else:
            shortfall = item_price - remaining
            message = (
                f"❌ **'{item_name}' is currently outside your budget.**\n\n"
                f"- Item price: **{sym}{item_price:,.2f}**\n"
                f"- Your remaining budget: **{sym}{remaining:,.2f}**\n"
                f"- You would need **{sym}{shortfall:,.2f}** more to afford this.\n\n"
                f"This is a budgeting calculation based on your entered data."
            )

        return affordable, message + DISCLAIMER
