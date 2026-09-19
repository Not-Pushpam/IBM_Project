"""Tests for ExpenseTracker."""

from __future__ import annotations

from datetime import date

import pytest

from financial_assistant.constants import ExpenseCategory
from financial_assistant.exceptions import (
    BudgetNotSetError,
    InvalidAmountError,
    InvalidCategoryError,
)
from financial_assistant.logic.budget_manager import BudgetManager
from financial_assistant.logic.expense_tracker import ExpenseTracker
from financial_assistant.storage.expense_repository import ExpenseRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TODAY = date.today()


def _setup(repo: ExpenseRepository) -> ExpenseTracker:
    """Create a tracker with a budget already set."""
    bm = BudgetManager(repo)
    bm.set_profile(2000.0, 1500.0)
    return ExpenseTracker(repo)


# ---------------------------------------------------------------------------
# add_expense — valid inputs
# ---------------------------------------------------------------------------

def test_add_expense_returns_expense_object(tmp_repo):
    tracker = _setup(tmp_repo)
    expense = tracker.add_expense("Food", "Groceries", 50.0, TODAY)
    assert expense.amount == 50.0
    assert expense.description == "Groceries"
    assert expense.category == ExpenseCategory.FOOD


def test_add_expense_assigns_unique_id(tmp_repo):
    tracker = _setup(tmp_repo)
    e1 = tracker.add_expense("Food", "Lunch", 10.0, TODAY)
    e2 = tracker.add_expense("Travel", "Bus", 3.0, TODAY)
    assert e1.expense_id != e2.expense_id


def test_add_expense_accepts_all_valid_categories(tmp_repo):
    tracker = _setup(tmp_repo)
    for cat in ExpenseCategory.values():
        tracker.add_expense(cat, "Test", 1.0, TODAY)
    assert len(tracker.get_all_expenses()) == len(ExpenseCategory.values())


def test_add_expense_accepts_enum_member_directly(tmp_repo):
    tracker = _setup(tmp_repo)
    expense = tracker.add_expense(ExpenseCategory.RENT, "Monthly rent", 600.0, TODAY)
    assert expense.category == ExpenseCategory.RENT


def test_add_expense_strips_description_whitespace(tmp_repo):
    tracker = _setup(tmp_repo)
    expense = tracker.add_expense("Food", "  Groceries  ", 20.0, TODAY)
    assert expense.description == "Groceries"


# ---------------------------------------------------------------------------
# add_expense — invalid inputs
# ---------------------------------------------------------------------------

def test_add_expense_rejects_zero_amount(tmp_repo):
    tracker = _setup(tmp_repo)
    with pytest.raises(InvalidAmountError):
        tracker.add_expense("Food", "Test", 0.0, TODAY)


def test_add_expense_rejects_negative_amount(tmp_repo):
    tracker = _setup(tmp_repo)
    with pytest.raises(InvalidAmountError):
        tracker.add_expense("Food", "Test", -10.0, TODAY)


def test_add_expense_rejects_empty_description(tmp_repo):
    tracker = _setup(tmp_repo)
    with pytest.raises(InvalidAmountError):
        tracker.add_expense("Food", "   ", 10.0, TODAY)


def test_add_expense_rejects_description_over_100_chars(tmp_repo):
    tracker = _setup(tmp_repo)
    long_desc = "x" * 101
    with pytest.raises(InvalidAmountError):
        tracker.add_expense("Food", long_desc, 10.0, TODAY)


def test_add_expense_rejects_invalid_category(tmp_repo):
    tracker = _setup(tmp_repo)
    with pytest.raises(InvalidCategoryError):
        tracker.add_expense("Gambling", "Casino", 50.0, TODAY)


def test_add_expense_raises_budget_not_set_when_no_profile(tmp_repo):
    tracker = ExpenseTracker(tmp_repo)  # no budget set
    with pytest.raises(BudgetNotSetError):
        tracker.add_expense("Food", "Test", 10.0, TODAY)


# ---------------------------------------------------------------------------
# get_all_expenses
# ---------------------------------------------------------------------------

def test_get_all_expenses_empty_initially(tmp_repo):
    tracker = _setup(tmp_repo)
    assert tracker.get_all_expenses() == []


def test_get_all_expenses_returns_added_expenses(tmp_repo):
    tracker = _setup(tmp_repo)
    tracker.add_expense("Food", "A", 10.0, TODAY)
    tracker.add_expense("Travel", "B", 20.0, TODAY)
    expenses = tracker.get_all_expenses()
    assert len(expenses) == 2


# ---------------------------------------------------------------------------
# get_total_spent
# ---------------------------------------------------------------------------

def test_get_total_spent_zero_when_no_expenses(tmp_repo):
    tracker = _setup(tmp_repo)
    assert tracker.get_total_spent() == pytest.approx(0.0)


def test_get_total_spent_sums_amounts(tmp_repo):
    tracker = _setup(tmp_repo)
    tracker.add_expense("Food", "A", 10.0, TODAY)
    tracker.add_expense("Travel", "B", 20.0, TODAY)
    tracker.add_expense("Shopping", "C", 5.0, TODAY)
    assert tracker.get_total_spent() == pytest.approx(35.0)


# ---------------------------------------------------------------------------
# remove_expense
# ---------------------------------------------------------------------------

def test_remove_expense_reduces_list(tmp_repo):
    tracker = _setup(tmp_repo)
    e = tracker.add_expense("Food", "Lunch", 12.0, TODAY)
    tracker.add_expense("Travel", "Bus", 3.0, TODAY)
    tracker.remove_expense(e.expense_id)
    remaining = tracker.get_all_expenses()
    assert len(remaining) == 1
    assert all(x.expense_id != e.expense_id for x in remaining)


def test_remove_expense_updates_total(tmp_repo):
    tracker = _setup(tmp_repo)
    e = tracker.add_expense("Food", "Lunch", 50.0, TODAY)
    tracker.add_expense("Travel", "Bus", 10.0, TODAY)
    tracker.remove_expense(e.expense_id)
    assert tracker.get_total_spent() == pytest.approx(10.0)
