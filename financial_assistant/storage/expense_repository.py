"""
ExpenseRepository — handles CSV-based persistence for expenses and the budget profile.

Design notes
------------
* All file I/O lives here; no other module reads or writes files directly.
* The repository uses two CSV files:
    - expenses.csv   → one row per Expense
    - profile.csv    → one row containing the BudgetProfile
* Both files are created automatically on first write.
* The class is also used as an in-memory store during a session (via the
  `_expenses` list and `_profile` attribute), so Streamlit never needs to
  re-read the file on every rerender.
"""

from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path
from typing import Optional

from financial_assistant.models.budget_profile import BudgetProfile
from financial_assistant.models.expense import Expense


# ---------------------------------------------------------------------------
# Default storage location — can be overridden in tests
# ---------------------------------------------------------------------------

DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"


class ExpenseRepository:
    """
    Manages in-memory storage and CSV persistence for expenses and the budget profile.

    Parameters
    ----------
    data_dir : Path | str, optional
        Directory where CSV files are stored.  Defaults to `<project>/data/`.
        Pass a temporary directory in tests so files don't pollute the repo.
    """

    EXPENSES_FILE = "expenses.csv"
    PROFILE_FILE = "profile.csv"

    # CSV column headers
    EXPENSE_FIELDS = ["expense_id", "category", "description", "amount", "date"]
    PROFILE_FIELDS = ["monthly_income", "monthly_budget", "currency_symbol"]

    def __init__(self, data_dir: Optional[Path | str] = None) -> None:
        self._data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self._data_dir.mkdir(parents=True, exist_ok=True)

        self._expenses: list[Expense] = []
        self._profile: Optional[BudgetProfile] = None

        self._load_all()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _expenses_path(self) -> Path:
        return self._data_dir / self.EXPENSES_FILE

    @property
    def _profile_path(self) -> Path:
        return self._data_dir / self.PROFILE_FILE

    def _load_all(self) -> None:
        """Load existing data from CSV files on startup."""
        self._load_profile()
        self._load_expenses()

    def _load_profile(self) -> None:
        if not self._profile_path.exists():
            return
        try:
            with open(self._profile_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._profile = BudgetProfile.from_dict(row)
                    break  # only one profile row
        except Exception:
            # Corrupted file — start fresh
            self._profile = None

    def _load_expenses(self) -> None:
        if not self._expenses_path.exists():
            return
        try:
            with open(self._expenses_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self._expenses = [Expense.from_dict(row) for row in reader]
        except Exception:
            self._expenses = []

    # ------------------------------------------------------------------
    # Budget profile
    # ------------------------------------------------------------------

    def get_profile(self) -> Optional[BudgetProfile]:
        return self._profile

    def save_profile(self, profile: BudgetProfile) -> None:
        self._profile = profile
        with open(self._profile_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.PROFILE_FIELDS)
            writer.writeheader()
            writer.writerow(profile.to_dict())

    # ------------------------------------------------------------------
    # Expenses
    # ------------------------------------------------------------------

    def get_expenses(self) -> list[Expense]:
        return list(self._expenses)

    def add_expense(self, expense: Expense) -> None:
        self._expenses.append(expense)
        self._persist_expenses()

    def remove_expense(self, expense_id: str) -> None:
        self._expenses = [e for e in self._expenses if e.expense_id != expense_id]
        self._persist_expenses()

    def clear_expenses(self) -> None:
        self._expenses = []
        self._persist_expenses()

    def _persist_expenses(self) -> None:
        with open(self._expenses_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.EXPENSE_FIELDS)
            writer.writeheader()
            for expense in self._expenses:
                writer.writerow(expense.to_dict())

    # ------------------------------------------------------------------
    # CSV export / import helpers (used by the Streamlit download/upload widgets)
    # ------------------------------------------------------------------

    def expenses_to_csv_string(self) -> str:
        """Return all expenses as a CSV-formatted string for download."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.EXPENSE_FIELDS)
        writer.writeheader()
        for expense in self._expenses:
            writer.writerow(expense.to_dict())
        return output.getvalue()

    def import_expenses_from_csv_string(self, csv_text: str) -> list[Expense]:
        """
        Parse a CSV string and return a list of Expense objects.
        Does NOT automatically save — caller decides whether to persist.
        """
        reader = csv.DictReader(io.StringIO(csv_text))
        return [Expense.from_dict(row) for row in reader]
