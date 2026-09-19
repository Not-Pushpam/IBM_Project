"""
Application-wide constants, enums and the disclaimer text used in all AI responses.
"""

from enum import Enum

# ---------------------------------------------------------------------------
# Expense categories
# ---------------------------------------------------------------------------

class ExpenseCategory(str, Enum):
    FOOD = "Food"
    TRAVEL = "Travel"
    SHOPPING = "Shopping"
    EDUCATION = "Education"
    RENT = "Rent"
    OTHER = "Other"

    @classmethod
    def values(cls) -> list[str]:
        return [c.value for c in cls]


# ---------------------------------------------------------------------------
# Validation thresholds
# ---------------------------------------------------------------------------

MAX_DESCRIPTION_LENGTH: int = 100
HIGH_SPEND_THRESHOLD: float = 0.50   # 50 % of budget → "high spend" warning
MAX_LOAN_MONTHS: int = 360           # 30 years
MAX_LOAN_RATE: float = 100.0         # percent

# ---------------------------------------------------------------------------
# Currency options shown in the UI
# ---------------------------------------------------------------------------

CURRENCY_OPTIONS: dict[str, str] = {
    "USD $": "$",
    "EUR €": "€",
    "GBP £": "£",
    "INR ₹": "₹",
}

# ---------------------------------------------------------------------------
# Standard disclaimer appended to every AI / advisor response
# ---------------------------------------------------------------------------

DISCLAIMER: str = (
    "\n\n---\n"
    "⚠️ **Educational purposes only.** This information is general financial literacy "
    "guidance and does not constitute professional financial advice. Please consult a "
    "qualified financial advisor before making important financial decisions."
)
