"""Net worth feature DTOs.

Data transfer objects for accounts and net worth tracking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Account:
    """A financial account for net worth tracking.

    Attributes:
        id: Database primary key, or None for unsaved accounts.
        name: Unique account name (e.g. "Chase Checking").
        account_type: One of "checking", "savings", "credit_card",
            "investment", "loan", or "other".
        balance: Current account balance in dollars.
        last_updated: Date of last balance update (ISO format).
        notes: Optional free-text notes about the account.

    Example:
        >>> account = Account(
        ...     id=1,
        ...     name="Chase Checking",
        ...     account_type="checking",
        ...     balance=2500.0,
        ...     last_updated="2024-01-15",
        ... )
        >>> account.name
        'Chase Checking'
    """

    id: int | None
    name: str
    account_type: str  # "checking", "savings", "credit_card", "investment", "loan", "other"
    balance: float
    last_updated: str  # ISO date format
    notes: str = ""


@dataclass
class NetWorthSummary:
    """Net worth summary with breakdown by account type.

    Attributes:
        total_assets: Sum of all asset account balances.
        total_liabilities: Sum of all liability account balances.
        net_worth: Total assets minus total liabilities.
        assets_by_type: Asset balances grouped by account type.
        liabilities_by_type: Liability balances grouped by type.
        accounts: All accounts included in the summary.

    Example:
        >>> summary = NetWorthSummary(
        ...     total_assets=10000.0,
        ...     total_liabilities=2000.0,
        ...     net_worth=8000.0,
        ...     assets_by_type={"checking": 5000.0, "savings": 5000.0},
        ...     liabilities_by_type={"credit_card": 2000.0},
        ...     accounts=[],
        ... )
        >>> summary.net_worth
        8000.0
    """

    total_assets: float
    total_liabilities: float
    net_worth: float
    assets_by_type: dict[str, float]
    liabilities_by_type: dict[str, float]
    accounts: list[Account]
