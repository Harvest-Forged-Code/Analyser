"""Re-categorize controller (thin facade).

Coordinates the recategorize service with the database layer
to re-apply keyword mappers to all stored transactions.
"""

from __future__ import annotations

import logging

from budget_analyser.features.recategorize.service import (
    RecategorizeResult,
    RecategorizeService,
)
from budget_analyser.infrastructure.database import TransactionDatabase


class RecategorizeController:
    """Controller that orchestrates transaction re-categorization.

    Fetches transactions from the database, delegates to the
    service for re-mapping, and persists changed rows.
    """

    def __init__(
        self,
        *,
        database: TransactionDatabase,
        service: RecategorizeService,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the recategorize controller.

        Args:
            database: TransactionDatabase for read/write access.
            service: RecategorizeService with current mappers.
            logger: Optional logger for diagnostics.
        """
        self._database = database
        self._service = service
        self._logger = logger or logging.getLogger(
            "budget_analyser.recategorize",
        )

    def run(self) -> RecategorizeResult:
        """Re-categorize all transactions in the database.

        Loads all transactions, re-applies keyword mappers,
        and batch-updates any rows whose categorization changed.

        Returns:
            RecategorizeResult with counts and status.

        Example:
            >>> result = controller.run()
            >>> result.success
            True
        """
        transactions = self._database.get_all_transactions()

        if transactions.empty:
            return RecategorizeResult(
                success=True,
                message="No transactions in database",
            )

        updated_df, result = self._service.recategorize(
            transactions=transactions,
        )

        if not updated_df.empty:
            self._database.update_categorization_batch(
                updates=updated_df,
            )
            self._logger.info(
                "Persisted %d re-categorized transactions",
                result.updated_count,
            )

        return result
