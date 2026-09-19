"""
Custom exception classes for the Financial Literacy Assistant.

All exceptions are raised by the business-logic layer and caught
by the Streamlit UI layer, which converts them into user-friendly messages.
"""


class InvalidAmountError(ValueError):
    """Raised when a monetary amount is zero, negative or non-numeric."""
    pass


class BudgetNotSetError(RuntimeError):
    """Raised when an operation requires a budget profile that has not yet been set."""
    pass


class InvalidDateError(ValueError):
    """Raised when an expense date is invalid (e.g. far in the future)."""
    pass


class InvalidCategoryError(ValueError):
    """Raised when a category value is not a member of ExpenseCategory."""
    pass


class InvalidLoanParameterError(ValueError):
    """Raised when loan parameters (principal, rate, duration) are out of range."""
    pass


class EmptyExpenseListError(RuntimeError):
    """Raised when analysis is requested but no expenses have been recorded."""
    pass
