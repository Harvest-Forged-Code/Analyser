"""Net worth feature DTOs.

Data transfer objects for accounts and net worth tracking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Account:
    """A financial account for net worth tracking."""

    id: int | None
    name: str
    account_type: str  # "checking", "savings", "credit_card", "investment", "loan", "other"
    balance: float
    last_updated: str  # ISO date format
    notes: str = ""


@dataclass
class NetWorthSummary:
    """Net worth summary with breakdown by account type."""

    total_assets: float
    total_liabilities: float
    net_worth: float
    assets_by_type: dict[str, float]
    liabilities_by_type: dict[str, float]
    accounts: list[Account]
