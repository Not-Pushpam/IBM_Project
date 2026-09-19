"""
Shared pytest fixtures — provides a clean in-memory ExpenseRepository
backed by a temporary directory so tests never read/write real files.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from financial_assistant.storage.expense_repository import ExpenseRepository


@pytest.fixture
def tmp_repo(tmp_path: Path) -> ExpenseRepository:
    """Return a fresh ExpenseRepository that writes to a temp directory."""
    return ExpenseRepository(data_dir=tmp_path)
