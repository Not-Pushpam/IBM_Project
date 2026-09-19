"""Tests for LoanCalculator."""

from __future__ import annotations

import pytest

from financial_assistant.advisor.loan_calculator import LoanCalculator
from financial_assistant.exceptions import InvalidLoanParameterError


@pytest.fixture
def calc() -> LoanCalculator:
    return LoanCalculator()


# ---------------------------------------------------------------------------
# calculate_emi — known values
# ---------------------------------------------------------------------------

def test_emi_known_value(calc):
    """
    $10,000 at 12% annual interest for 12 months.
    Standard formula gives ≈ $888.49.
    """
    emi = calc.calculate_emi(10_000.0, 12.0, 12)
    assert emi == pytest.approx(888.49, abs=0.01)


def test_emi_zero_interest_equals_principal_divided_by_months(calc):
    emi = calc.calculate_emi(1_200.0, 0.0, 12)
    assert emi == pytest.approx(100.0)


def test_emi_single_month(calc):
    """Single-month loan: EMI should be very close to principal + one month's interest."""
    emi = calc.calculate_emi(1_000.0, 12.0, 1)
    expected = 1_000.0 * (12 / 12 / 100) * (1 + 12 / 12 / 100) ** 1 / ((1 + 12 / 12 / 100) ** 1 - 1)
    assert emi == pytest.approx(expected, abs=0.01)


def test_emi_long_tenure(calc):
    """30-year mortgage: sanity check that EMI is positive and reasonable."""
    emi = calc.calculate_emi(100_000.0, 6.0, 360)
    assert 500.0 < emi < 700.0


# ---------------------------------------------------------------------------
# calculate_total_repayment
# ---------------------------------------------------------------------------

def test_total_repayment_equals_emi_times_months(calc):
    emi = calc.calculate_emi(10_000.0, 12.0, 12)
    total = calc.calculate_total_repayment(10_000.0, 12.0, 12)
    assert total == pytest.approx(emi * 12, abs=0.02)


# ---------------------------------------------------------------------------
# calculate_total_interest
# ---------------------------------------------------------------------------

def test_total_interest_is_non_negative(calc):
    interest = calc.calculate_total_interest(10_000.0, 12.0, 12)
    assert interest >= 0


def test_total_interest_zero_for_zero_rate(calc):
    interest = calc.calculate_total_interest(1_200.0, 0.0, 12)
    assert interest == pytest.approx(0.0, abs=0.01)


def test_total_repayment_equals_principal_plus_interest(calc):
    principal = 10_000.0
    rate = 12.0
    months = 12
    total = calc.calculate_total_repayment(principal, rate, months)
    interest = calc.calculate_total_interest(principal, rate, months)
    assert total == pytest.approx(principal + interest, abs=0.02)


# ---------------------------------------------------------------------------
# Validation — invalid parameters
# ---------------------------------------------------------------------------

def test_emi_raises_for_zero_principal(calc):
    with pytest.raises(InvalidLoanParameterError):
        calc.calculate_emi(0.0, 12.0, 12)


def test_emi_raises_for_negative_principal(calc):
    with pytest.raises(InvalidLoanParameterError):
        calc.calculate_emi(-1000.0, 12.0, 12)


def test_emi_raises_for_negative_rate(calc):
    with pytest.raises(InvalidLoanParameterError):
        calc.calculate_emi(1000.0, -1.0, 12)


def test_emi_raises_for_rate_over_100(calc):
    with pytest.raises(InvalidLoanParameterError):
        calc.calculate_emi(1000.0, 101.0, 12)


def test_emi_raises_for_zero_months(calc):
    with pytest.raises(InvalidLoanParameterError):
        calc.calculate_emi(1000.0, 12.0, 0)


def test_emi_raises_for_months_over_360(calc):
    with pytest.raises(InvalidLoanParameterError):
        calc.calculate_emi(1000.0, 12.0, 361)


# ---------------------------------------------------------------------------
# explain_emi
# ---------------------------------------------------------------------------

def test_explain_emi_contains_principal(calc):
    explanation = calc.explain_emi(10_000.0, 12.0, 12)
    assert "10,000" in explanation


def test_explain_emi_contains_emi_value(calc):
    explanation = calc.explain_emi(10_000.0, 12.0, 12)
    assert "888" in explanation  # 888.49 rounded


def test_explain_emi_contains_disclaimer(calc):
    explanation = calc.explain_emi(10_000.0, 12.0, 12)
    assert "educational" in explanation.lower() or "⚠️" in explanation


def test_explain_emi_uses_currency_symbol(calc):
    explanation = calc.explain_emi(1_000.0, 10.0, 12, currency_symbol="£")
    assert "£" in explanation
