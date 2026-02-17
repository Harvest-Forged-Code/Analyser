"""Net worth service.

Pure business logic for net worth calculations.
No PySide6 or infrastructure dependencies.
"""

from __future__ import annotations

from budget_analyser.features.net_worth.models import Account, NetWorthSummary

ASSET_TYPES = frozenset({"checking", "savings", "investment", "other"})
LIABILITY_TYPES = frozenset({"credit_card", "loan"})


def calculate_net_worth_summary(
    *,
    accounts: list[Account],
) -> NetWorthSummary:
    """Calculate comprehensive net worth summary from accounts.

    Groups accounts into assets vs. liabilities by account type
    and computes totals. Asset types are checking, savings,
    investment, and other. Liability types are credit_card and loan.

    Args:
        accounts: All financial accounts to include.

    Returns:
        NetWorthSummary with totals and per-type breakdowns.

    Example:
        >>> accounts = [
        ...     Account(
        ...         id=1, name="Checking",
        ...         account_type="checking", balance=5000.0,
        ...         last_updated="2024-01-15",
        ...     ),
        ...     Account(
        ...         id=2, name="Credit Card",
        ...         account_type="credit_card", balance=-2000.0,
        ...         last_updated="2024-01-15",
        ...     ),
        ... ]
        >>> summary = calculate_net_worth_summary(accounts=accounts)
        >>> summary.net_worth
        3000.0
    """
    assets_by_type: dict[str, float] = {}
    liabilities_by_type: dict[str, float] = {}

    for account in accounts:
        if account.account_type in ASSET_TYPES:
            assets_by_type[account.account_type] = (
                assets_by_type.get(account.account_type, 0.0)
                + account.balance
            )
        elif account.account_type in LIABILITY_TYPES:
            liabilities_by_type[account.account_type] = (
                liabilities_by_type.get(account.account_type, 0.0)
                + abs(account.balance)
            )

    total_assets = sum(assets_by_type.values())
    total_liabilities = sum(liabilities_by_type.values())

    return NetWorthSummary(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=total_assets - total_liabilities,
        assets_by_type=assets_by_type,
        liabilities_by_type=liabilities_by_type,
        accounts=accounts,
    )
