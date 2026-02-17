"""Net worth controller.

Thin facade that delegates to repository for persistence
and service for business logic.
"""

from __future__ import annotations

from budget_analyser.features.net_worth.models import Account, NetWorthSummary
from budget_analyser.features.net_worth.repository import NetWorthRepository
from budget_analyser.features.net_worth.service import (
    calculate_net_worth_summary,
)


class NetWorthController:
    """Controller for net worth and accounts management.

    Provides the same API surface as the legacy BudgetController
    net-worth methods, but delegates to the feature repository
    and service.

    Example:
        >>> from pathlib import Path
        >>> repo = NetWorthRepository(db_path=Path("budget.db"))
        >>> ctrl = NetWorthController(repository=repo)
        >>> summary = ctrl.get_net_worth_summary()
        >>> summary.net_worth
        8000.0
    """

    def __init__(self, *, repository: NetWorthRepository) -> None:
        """Initialize the net worth controller.

        Args:
            repository: Net worth repository for persistence.

        Example:
            >>> ctrl = NetWorthController(repository=repo)
        """
        self._repository = repository

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
            >>> ctrl.add_account(
            ...     "Chase Checking", "checking", 2500.0,
            ... )
            Account(id=1, name='Chase Checking', ...)
        """
        return self._repository.add_account(
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
            >>> ctrl.update_account_balance(1, 3000.0)
            True
        """
        return self._repository.update_account_balance(
            account_id, balance,
        )

    def get_all_accounts(self) -> list[Account]:
        """Get all financial accounts.

        Returns:
            List of all accounts.

        Example:
            >>> accounts = ctrl.get_all_accounts()
            >>> len(accounts)
            3
        """
        return self._repository.get_all_accounts()

    def delete_account(self, account_id: int) -> bool:
        """Delete a financial account.

        Args:
            account_id: The account ID to delete.

        Returns:
            True if an account was deleted.

        Example:
            >>> ctrl.delete_account(1)
            True
        """
        return self._repository.delete_account(account_id)

    def get_net_worth_summary(self) -> NetWorthSummary:
        """Get comprehensive net worth summary.

        Fetches all accounts and computes assets, liabilities,
        and net worth totals.

        Returns:
            NetWorthSummary with totals and per-type breakdowns.

        Example:
            >>> summary = ctrl.get_net_worth_summary()
            >>> summary.net_worth
            8000.0
        """
        accounts = self._repository.get_all_accounts()
        return calculate_net_worth_summary(accounts=accounts)
