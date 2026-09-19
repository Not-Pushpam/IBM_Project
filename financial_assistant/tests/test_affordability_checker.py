"""Tests for AffordabilityChecker."""

from __future__ import annotations

from datetime import date

import pytest

from financial_assistant.constants import DISCLAIMER
from financial_assistant.exceptions import BudgetNotSetError, InvalidAmountError
from financial_assistant.logic.affordability_checker import AffordabilityChecker
from financial_assistant.logic.budget_manager import BudgetManager
from financial_assistant.logic.expense_tracker import ExpenseTracker
from financial_assistant.storage.expense_repository import ExpenseRepository


TODAY = date.today()


def _setup(repo: ExpenseRepository) -> tuple[ExpenseTracker, AffordabilityChecker]:
    bm = BudgetManager(repo)
    bm.set_profile(2000.0, 1000.0)
    tracker = ExpenseTracker(repo)
    checker = AffordabilityChecker(repo)
    return tracker, checker


# ---------------------------------------------------------------------------
# can_afford (pure helper)
# ---------------------------------------------------------------------------

def test_can_afford_true_when_price_less_than_remaining(tmp_repo):
    _, checker = _setup(tmp_repo)
    assert checker.can_afford(100.0, 500.0) is True


def test_can_afford_true_when_price_equals_remaining(tmp_repo):
    """Boundary: exactly equal is considered affordable."""
    _, checker = _setup(tmp_repo)
    assert checker.can_afford(500.0, 500.0) is True


def test_can_afford_false_when_price_exceeds_remaining(tmp_repo):
    _, checker = _setup(tmp_repo)
    assert checker.can_afford(600.0, 500.0) is False


# ---------------------------------------------------------------------------
# check — valid scenarios
# ---------------------------------------------------------------------------

def test_check_affordable_item(tmp_repo):
    tracker, checker = _setup(tmp_repo)
    # Spent 200, budget 1000 → remaining 800
    tracker.add_expense("Food", "Groceries", 200.0, TODAY)
    affordable, message = checker.check("Laptop", 500.0, total_spent=200.0)

    assert affordable is True
    assert "Laptop" in message
    assert "300.00" in message  # remaining after purchase


def test_check_unaffordable_item(tmp_repo):
    tracker, checker = _setup(tmp_repo)
    tracker.add_expense("Rent", "Apartment", 900.0, TODAY)
    affordable, message = checker.check("New Phone", 200.0, total_spent=900.0)

    assert affordable is False
    assert "New Phone" in message


def test_check_message_contains_disclaimer(tmp_repo):
    _, checker = _setup(tmp_repo)
    _, message = checker.check("Book", 10.0, total_spent=0.0)
    assert "educational purposes" in message.lower() or "disclaimer" in message.lower() or "⚠️" in message


def test_check_item_exactly_equal_to_remaining(tmp_repo):
    """Boundary: affordable when price equals remaining budget exactly."""
    _, checker = _setup(tmp_repo)
    # budget 1000, spent 0 → remaining 1000
    affordable, _ = checker.check("Perfect item", 1000.0, total_spent=0.0)
    assert affordable is True


# ---------------------------------------------------------------------------
# check — invalid inputs
# ---------------------------------------------------------------------------

def test_check_raises_for_zero_price(tmp_repo):
    _, checker = _setup(tmp_repo)
    with pytest.raises(InvalidAmountError):
        checker.check("Item", 0.0, total_spent=0.0)


def test_check_raises_for_negative_price(tmp_repo):
    _, checker = _setup(tmp_repo)
    with pytest.raises(InvalidAmountError):
        checker.check("Item", -50.0, total_spent=0.0)


def test_check_raises_budget_not_set(tmp_repo):
    checker = AffordabilityChecker(tmp_repo)  # no budget set
    with pytest.raises(BudgetNotSetError):
        checker.check("Item", 100.0, total_spent=0.0)
