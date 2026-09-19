"""Tests for BudgetManager."""

from __future__ import annotations

import pytest

from financial_assistant.exceptions import BudgetNotSetError, InvalidAmountError
from financial_assistant.logic.budget_manager import BudgetManager
from financial_assistant.storage.expense_repository import ExpenseRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_bm(tmp_repo: ExpenseRepository) -> BudgetManager:
    return BudgetManager(tmp_repo)


# ---------------------------------------------------------------------------
# set_profile — valid inputs
# ---------------------------------------------------------------------------

def test_set_profile_stores_income_and_budget(tmp_repo):
    bm = make_bm(tmp_repo)
    profile = bm.set_profile(monthly_income=2000.0, monthly_budget=1500.0)
    assert profile.monthly_income == 2000.0
    assert profile.monthly_budget == 1500.0


def test_set_profile_stores_currency_symbol(tmp_repo):
    bm = make_bm(tmp_repo)
    profile = bm.set_profile(1000.0, 800.0, currency_symbol="£")
    assert profile.currency_symbol == "£"


def test_set_profile_allows_zero_income(tmp_repo):
    """Income of 0 is allowed (e.g. student with allowance only)."""
    bm = make_bm(tmp_repo)
    profile = bm.set_profile(monthly_income=0.0, monthly_budget=500.0)
    assert profile.monthly_income == 0.0


def test_set_profile_budget_equal_to_income(tmp_repo):
    bm = make_bm(tmp_repo)
    profile = bm.set_profile(1000.0, 1000.0)
    assert profile.monthly_budget == 1000.0


# ---------------------------------------------------------------------------
# set_profile — invalid inputs
# ---------------------------------------------------------------------------

def test_set_profile_rejects_negative_income(tmp_repo):
    bm = make_bm(tmp_repo)
    with pytest.raises(InvalidAmountError):
        bm.set_profile(monthly_income=-100.0, monthly_budget=500.0)


def test_set_profile_rejects_zero_budget(tmp_repo):
    bm = make_bm(tmp_repo)
    with pytest.raises(InvalidAmountError):
        bm.set_profile(monthly_income=1000.0, monthly_budget=0.0)


def test_set_profile_rejects_negative_budget(tmp_repo):
    bm = make_bm(tmp_repo)
    with pytest.raises(InvalidAmountError):
        bm.set_profile(monthly_income=1000.0, monthly_budget=-200.0)


# ---------------------------------------------------------------------------
# get_profile
# ---------------------------------------------------------------------------

def test_get_profile_raises_when_not_set(tmp_repo):
    bm = make_bm(tmp_repo)
    with pytest.raises(BudgetNotSetError):
        bm.get_profile()


def test_get_profile_returns_saved_profile(tmp_repo):
    bm = make_bm(tmp_repo)
    bm.set_profile(2000.0, 1500.0)
    profile = bm.get_profile()
    assert profile.monthly_income == 2000.0


# ---------------------------------------------------------------------------
# get_remaining_budget
# ---------------------------------------------------------------------------

def test_remaining_budget_no_spending(tmp_repo):
    bm = make_bm(tmp_repo)
    bm.set_profile(2000.0, 1500.0)
    assert bm.get_remaining_budget(0.0) == pytest.approx(1500.0)


def test_remaining_budget_with_spending(tmp_repo):
    bm = make_bm(tmp_repo)
    bm.set_profile(2000.0, 1500.0)
    assert bm.get_remaining_budget(400.0) == pytest.approx(1100.0)


def test_remaining_budget_negative_when_over(tmp_repo):
    bm = make_bm(tmp_repo)
    bm.set_profile(2000.0, 1000.0)
    assert bm.get_remaining_budget(1200.0) == pytest.approx(-200.0)


# ---------------------------------------------------------------------------
# is_over_budget
# ---------------------------------------------------------------------------

def test_is_over_budget_false_when_under(tmp_repo):
    bm = make_bm(tmp_repo)
    bm.set_profile(2000.0, 1000.0)
    assert bm.is_over_budget(800.0) is False


def test_is_over_budget_false_when_exactly_equal(tmp_repo):
    bm = make_bm(tmp_repo)
    bm.set_profile(2000.0, 1000.0)
    assert bm.is_over_budget(1000.0) is False


def test_is_over_budget_true_when_over(tmp_repo):
    bm = make_bm(tmp_repo)
    bm.set_profile(2000.0, 1000.0)
    assert bm.is_over_budget(1001.0) is True


# ---------------------------------------------------------------------------
# budget_exceeds_income
# ---------------------------------------------------------------------------

def test_budget_does_not_exceed_income(tmp_repo):
    bm = make_bm(tmp_repo)
    bm.set_profile(2000.0, 1500.0)
    assert bm.budget_exceeds_income() is False


def test_budget_exceeds_income_returns_true(tmp_repo):
    bm = make_bm(tmp_repo)
    bm.set_profile(1000.0, 1500.0)
    assert bm.budget_exceeds_income() is True
