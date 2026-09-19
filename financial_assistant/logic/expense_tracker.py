"""
ExpenseTracker — adds, lists and totals the student's expenses.
"""

from __future__ import annotations

from datetime import date

from financial_assistant.constants import ExpenseCategory, MAX_DESCRIPTION_LENGTH
from financial_assistant.exceptions import (
    BudgetNotSetError,
    InvalidAmountError,
    InvalidCategoryError,
)
from financial_assistant.models.expense import Expense
from financial_assistant.storage.expense_repository import ExpenseRepository


class ExpenseTracker:
    """
    Manages expense entries.

    Responsibilities
    ----------------
    * Validate and add new expenses.
    * Retrieve all expenses.
    * Calculate total spending.
    * Remove a specific expense by ID.

    Parameters
    ----------
    repository : ExpenseRepository
        Shared data store injected from the outside.
    """

    def __init__(self, repository: ExpenseRepository) -> None:
        self._repo = repository

    # ------------------------------------------------------------------
    # Add / remove
    # ------------------------------------------------------------------

    def add_expense(
        self,
        category: str | ExpenseCategory,
        description: str,
        amount: float,
        expense_date: date,
    ) -> Expense:
        """
        Validate inputs and persist a new expense.

        Returns
        -------
        Expense
            The newly created expense object.

        Raises
        ------
        BudgetNotSetError
            If no budget profile exists.
        InvalidAmountError
            If amount <= 0 or description is empty / too long.
        InvalidCategoryError
            If category is not a recognised ExpenseCategory value.
        """
        # Require a budget to be set first
        if self._repo.get_profile() is None:
            raise BudgetNotSetError(
                "Please set your income and budget before adding expenses."
            )

        # Validate category
        if isinstance(category, str):
            try:
                category = ExpenseCategory(category)
            except ValueError:
                raise InvalidCategoryError(
                    f"'{category}' is not a valid category. "
                    f"Choose from: {', '.join(ExpenseCategory.values())}"
                )

        # Validate amount
        if amount <= 0:
            raise InvalidAmountError("Expense amount must be greater than zero.")

        # Validate description
        description = description.strip()
        if not description:
            raise InvalidAmountError("Please enter a short description for the expense.")
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise InvalidAmountError(
                f"Description is too long. Maximum {MAX_DESCRIPTION_LENGTH} characters."
            )

        expense = Expense(
            category=category,
            description=description,
            amount=amount,
            date=expense_date,
        )
        self._repo.add_expense(expense)
        return expense

    def remove_expense(self, expense_id: str) -> None:
        """Remove the expense with the given ID."""
        self._repo.remove_expense(expense_id)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_all_expenses(self) -> list[Expense]:
        """Return all stored expenses."""
        return self._repo.get_expenses()

    def get_total_spent(self) -> float:
        """Return the sum of all expense amounts."""
        return sum(e.amount for e in self._repo.get_expenses())
