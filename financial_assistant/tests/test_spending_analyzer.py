"""Tests for SpendingAnalyzer."""

from __future__ import annotations

from datetime import date

import pytest

from financial_assistant.exceptions import BudgetNotSetError, EmptyExpenseListError
from financial_assistant.logic.budget_manager import BudgetManager
from financial_assistant.logic.expense_tracker import ExpenseTracker
from financial_assistant.logic.spending_analyzer import SpendingAnalyzer
from financial_assistant.storage.expense_repository import ExpenseRepository


TODAY = date.today()


def _setup(repo: ExpenseRepository):
    bm = BudgetManager(repo)
    bm.set_profile(2000.0, 1000.0)
    tracker = ExpenseTracker(repo)
    analyzer = SpendingAnalyzer(repo)
    return tracker, analyzer


# ---------------------------------------------------------------------------
# get_category_totals
# ---------------------------------------------------------------------------

def test_get_category_totals_raises_when_no_expenses(tmp_repo):
    _, analyzer = _setup(tmp_repo)
    with pytest.raises(EmptyExpenseListError):
        analyzer.get_category_totals()


def test_get_category_totals_correct_sums(tmp_repo):
    tracker, analyzer = _setup(tmp_repo)
    tracker.add_expense("Food", "A", 100.0, TODAY)
    tracker.add_expense("Food", "B", 50.0, TODAY)
    tracker.add_expense("Travel", "C", 30.0, TODAY)

    totals = analyzer.get_category_totals()
    assert totals["Food"] == pytest.approx(150.0)
    assert totals["Travel"] == pytest.approx(30.0)


def test_get_category_totals_excludes_zero_categories(tmp_repo):
    tracker, analyzer = _setup(tmp_repo)
    tracker.add_expense("Food", "Lunch", 20.0, TODAY)

    totals = analyzer.get_category_totals()
    # Only Food should appear — zero-spend categories are filtered out
    assert "Travel" not in totals
    assert "Food" in totals


# ---------------------------------------------------------------------------
# get_highest_spending_category
# ---------------------------------------------------------------------------

def test_get_highest_spending_category(tmp_repo):
    tracker, analyzer = _setup(tmp_repo)
    tracker.add_expense("Food", "A", 200.0, TODAY)
    tracker.add_expense("Travel", "B", 50.0, TODAY)
    tracker.add_expense("Shopping", "C", 150.0, TODAY)

    assert analyzer.get_highest_spending_category() == "Food"


def test_get_highest_spending_category_single_expense(tmp_repo):
    tracker, analyzer = _setup(tmp_repo)
    tracker.add_expense("Rent", "Apartment", 600.0, TODAY)

    assert analyzer.get_highest_spending_category() == "Rent"


# ---------------------------------------------------------------------------
# is_category_over_threshold
# ---------------------------------------------------------------------------

def test_category_not_over_threshold(tmp_repo):
    tracker, analyzer = _setup(tmp_repo)
    tracker.add_expense("Food", "Lunch", 100.0, TODAY)  # 100 / 1000 = 10% < 50%

    assert analyzer.is_category_over_threshold("Food", budget=1000.0) is False


def test_category_over_threshold(tmp_repo):
    tracker, analyzer = _setup(tmp_repo)
    tracker.add_expense("Rent", "Apartment", 600.0, TODAY)  # 600 / 1000 = 60% > 50%

    assert analyzer.is_category_over_threshold("Rent", budget=1000.0) is True


def test_category_exactly_at_threshold_is_not_over(tmp_repo):
    tracker, analyzer = _setup(tmp_repo)
    tracker.add_expense("Food", "Groceries", 500.0, TODAY)  # exactly 50%

    assert analyzer.is_category_over_threshold("Food", budget=1000.0) is False


# ---------------------------------------------------------------------------
# get_spending_patterns
# ---------------------------------------------------------------------------

def test_get_spending_patterns_raises_when_no_budget(tmp_repo):
    analyzer = SpendingAnalyzer(tmp_repo)  # no budget set
    with pytest.raises(BudgetNotSetError):
        analyzer.get_spending_patterns()


def test_get_spending_patterns_raises_when_no_expenses(tmp_repo):
    _, analyzer = _setup(tmp_repo)
    with pytest.raises(EmptyExpenseListError):
        analyzer.get_spending_patterns()


def test_get_spending_patterns_returns_list_of_strings(tmp_repo):
    tracker, analyzer = _setup(tmp_repo)
    tracker.add_expense("Food", "A", 100.0, TODAY)

    patterns = analyzer.get_spending_patterns()
    assert isinstance(patterns, list)
    assert len(patterns) >= 1
    assert all(isinstance(p, str) for p in patterns)


def test_get_spending_patterns_mentions_top_category(tmp_repo):
    tracker, analyzer = _setup(tmp_repo)
    tracker.add_expense("Rent", "Apartment", 800.0, TODAY)

    patterns = analyzer.get_spending_patterns()
    combined = " ".join(patterns)
    assert "Rent" in combined


def test_get_spending_patterns_detects_over_budget(tmp_repo):
    tracker, analyzer = _setup(tmp_repo)
    # Budget is 1000; spend 1200 → over budget
    tracker.add_expense("Shopping", "Splurge", 1200.0, TODAY)

    patterns = analyzer.get_spending_patterns()
    combined = " ".join(patterns)
    assert "over budget" in combined.lower()
