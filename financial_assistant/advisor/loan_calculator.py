"""
LoanCalculator — educational EMI and interest calculations.

All methods are pure functions (no side-effects, no file I/O).
Results are accompanied by plain-English explanations aimed at students.
"""

from __future__ import annotations

from financial_assistant.constants import DISCLAIMER, MAX_LOAN_MONTHS, MAX_LOAN_RATE
from financial_assistant.exceptions import InvalidLoanParameterError


class LoanCalculator:
    """
    Provides basic loan calculation and educational explanations.

    This calculator is for **educational purposes only**.
    Actual loan terms vary by lender and are subject to change.
    """

    # ------------------------------------------------------------------
    # Validation helper
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(principal: float, annual_rate: float, months: int) -> None:
        if principal <= 0:
            raise InvalidLoanParameterError("Loan amount must be greater than zero.")
        if annual_rate < 0:
            raise InvalidLoanParameterError("Interest rate cannot be negative.")
        if annual_rate > MAX_LOAN_RATE:
            raise InvalidLoanParameterError(
                f"Interest rate cannot exceed {MAX_LOAN_RATE}%."
            )
        if months < 1:
            raise InvalidLoanParameterError("Loan tenure must be at least 1 month.")
        if months > MAX_LOAN_MONTHS:
            raise InvalidLoanParameterError(
                f"Loan tenure cannot exceed {MAX_LOAN_MONTHS} months (30 years)."
            )

    # ------------------------------------------------------------------
    # Core calculations
    # ------------------------------------------------------------------

    def calculate_emi(
        self, principal: float, annual_rate: float, months: int
    ) -> float:
        """
        Calculate the Equated Monthly Instalment (EMI).

        Formula (standard reducing-balance):
            EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        where r = annual_rate / 12 / 100 and n = months.

        Special case: when annual_rate == 0, EMI = principal / months.

        Raises
        ------
        InvalidLoanParameterError
            If any parameter is out of the allowed range.
        """
        self._validate(principal, annual_rate, months)

        if annual_rate == 0:
            return round(principal / months, 2)

        r = annual_rate / 12 / 100
        emi = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
        return round(emi, 2)

    def calculate_total_repayment(
        self, principal: float, annual_rate: float, months: int
    ) -> float:
        """Return total amount repaid over the full loan tenure."""
        emi = self.calculate_emi(principal, annual_rate, months)
        return round(emi * months, 2)

    def calculate_total_interest(
        self, principal: float, annual_rate: float, months: int
    ) -> float:
        """Return the total interest paid (total repayment minus principal)."""
        total = self.calculate_total_repayment(principal, annual_rate, months)
        return round(total - principal, 2)

    # ------------------------------------------------------------------
    # Educational explanation
    # ------------------------------------------------------------------

    def explain_emi(
        self,
        principal: float,
        annual_rate: float,
        months: int,
        currency_symbol: str = "$",
    ) -> str:
        """
        Return a multi-paragraph plain-English explanation of the loan.

        Includes: what each term means, the calculated EMI, total interest,
        and the total repayment amount, followed by the standard disclaimer.
        """
        self._validate(principal, annual_rate, months)

        emi = self.calculate_emi(principal, annual_rate, months)
        total_repayment = self.calculate_total_repayment(principal, annual_rate, months)
        total_interest = self.calculate_total_interest(principal, annual_rate, months)
        sym = currency_symbol
        years = months // 12
        rem_months = months % 12
        tenure_str = (
            f"{years} year(s) and {rem_months} month(s)"
            if years > 0
            else f"{months} month(s)"
        )

        return (
            f"### 📘 Loan Breakdown\n\n"
            f"**Principal** (the amount you borrow): **{sym}{principal:,.2f}**\n\n"
            f"**Annual interest rate**: **{annual_rate:.2f}%**\n"
            f"  - This means the lender charges {annual_rate:.2f}% of the outstanding "
            f"balance every year as the cost of borrowing.\n\n"
            f"**Loan tenure**: **{tenure_str}** ({months} monthly payments)\n\n"
            f"---\n\n"
            f"**Your estimated monthly EMI**: **{sym}{emi:,.2f}**\n"
            f"  - EMI (Equated Monthly Instalment) is the fixed amount you pay every "
            f"month until the loan is fully repaid.\n\n"
            f"**Total interest you will pay**: **{sym}{total_interest:,.2f}**\n"
            f"  - This is the extra cost of borrowing, on top of the original amount.\n\n"
            f"**Total repayment amount**: **{sym}{total_repayment:,.2f}**\n"
            f"  - Principal ({sym}{principal:,.2f}) + Interest ({sym}{total_interest:,.2f})\n"
        ) + DISCLAIMER

    # ------------------------------------------------------------------
    # Loan glossary
    # ------------------------------------------------------------------

    @staticmethod
    def get_loan_glossary() -> str:
        """Return a plain-English glossary of common loan terms."""
        return (
            "### 📖 Loan Concepts — Quick Guide\n\n"
            "**Principal** — The original amount of money you borrow.\n\n"
            "**Interest** — The fee charged by the lender for lending you money.\n\n"
            "**Interest Rate** — The percentage of the outstanding loan balance "
            "charged as interest, usually quoted per year (annual rate).\n\n"
            "**EMI (Equated Monthly Instalment)** — A fixed monthly payment that "
            "covers both a portion of the principal and the interest. You pay this "
            "every month until the loan is cleared.\n\n"
            "**Loan Tenure** — The total length of time over which you repay the "
            "loan (e.g. 12 months, 36 months, 60 months).\n\n"
            "**Total Repayment** — The full amount you pay back: principal + all "
            "interest charges.\n\n"
            "**Prepayment** — Paying off part or all of the loan early, which reduces "
            "the total interest you pay.\n\n"
            "**Default** — Failing to make scheduled repayments. This damages your "
            "credit history and may lead to legal consequences.\n\n"
            + DISCLAIMER
        )
