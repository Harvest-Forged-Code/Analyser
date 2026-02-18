"""Net worth service.

Business logic and orchestration for net worth calculations.
Combines pure functions with model delegation for account management.
"""

from __future__ import annotations

from budget_analyser.features.net_worth.models import (
    Account,
    NetWorthModel,
    NetWorthSummary,
)

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


class NetWorthService:
    """Service for net worth and accounts management.

    Delegates persistence to NetWorthModel and uses pure functions
    for business logic calculations.

    Example:
        >>> from pathlib import Path
        >>> model = NetWorthModel(db_path=Path("budget.db"))
        >>> svc = NetWorthService(model=model)
        >>> summary = svc.get_net_worth_summary()
        >>> summary.net_worth
        8000.0
    """

    def __init__(self, *, model: NetWorthModel) -> None:
        """Initialize the net worth service.

        Args:
            model: Net worth model for persistence.

        Example:
            >>> svc = NetWorthService(model=model)
        """
        self._model = model

    def add_account(
        self,
        name: str,
        account_type: str,
        balance: float = 0,
        notes: str = "",
    ) -> Account:
        """Add a new financial account.

        Args:
            name: Unique account name.
            account_type: Type of account.
            balance: Initial balance.
            notes: Optional notes.

        Returns:
            The created Account.

        Example:
            >>> svc.add_account(
            ...     "Chase Checking", "checking", 2500.0,
            ... )
            Account(id=1, name='Chase Checking', ...)
        """
        return self._model.add_account(
            name, account_type, balance, notes,
        )

    def update_account_balance(
        self,
        account_id: int,
        balance: float,
    ) -> bool:
        """Update an account's balance.

        Args:
            account_id: The account ID to update.
            balance: The new balance.

        Returns:
            True if the account was updated.

        Example:
            >>> svc.update_account_balance(1, 3000.0)
            True
        """
        return self._model.update_account_balance(
            account_id, balance,
        )

    def get_all_accounts(self) -> list[Account]:
        """Get all financial accounts.

        Returns:
            List of all accounts.

        Example:
            >>> accounts = svc.get_all_accounts()
            >>> len(accounts)
            3
        """
        return self._model.get_all_accounts()

    def delete_account(self, account_id: int) -> bool:
        """Delete a financial account.

        Args:
            account_id: The account ID to delete.

        Returns:
            True if an account was deleted.

        Example:
            >>> svc.delete_account(1)
            True
        """
        return self._model.delete_account(account_id)

    def get_net_worth_summary(self) -> NetWorthSummary:
        """Get comprehensive net worth summary.

        Fetches all accounts and computes assets, liabilities,
        and net worth totals.

        Returns:
            NetWorthSummary with totals and per-type breakdowns.

        Example:
            >>> summary = svc.get_net_worth_summary()
            >>> summary.net_worth
            8000.0
        """
        accounts = self._model.get_all_accounts()
        return calculate_net_worth_summary(accounts=accounts)


NetWorthController = NetWorthService
