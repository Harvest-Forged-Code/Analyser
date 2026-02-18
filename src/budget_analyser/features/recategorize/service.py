"""Re-categorize service (business logic + orchestration).

Provides pure re-categorization logic and an orchestrator that
coordinates database access with the re-categorization service.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from budget_analyser.features.ingestion.categorization import (
    CategoryMappers,
    map_by_keywords_substring,
    map_by_keywords_exact,
)
from budget_analyser.core.database import TransactionDatabase


@dataclass(frozen=True)
class RecategorizeResult:
    """Result of a re-categorization run.

    Attributes:
        success: Whether the operation completed without errors.
        message: Human-readable summary.
        total_transactions: Number of transactions examined.
        updated_count: Number of rows whose categorization changed.
    """

    success: bool
    message: str = ""
    total_transactions: int = 0
    updated_count: int = 0


class RecategorizeService:
    """Service that re-applies keyword mappers to stored transactions.

    Compares current DB categorization against the latest mapper
    files and batch-updates any rows that differ.
    """

    def __init__(
        self,
        *,
        category_mappers: CategoryMappers,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the recategorize service.

        Args:
            category_mappers: Current keyword mappers to apply.
            logger: Optional logger for diagnostics.
        """
        self._mappers = category_mappers
        self._logger = logger or logging.getLogger(
            "budget_analyser.recategorize",
        )

    def recategorize(
        self, *, transactions: pd.DataFrame,
    ) -> tuple[pd.DataFrame, RecategorizeResult]:
        """Re-apply mappers and return updated rows.

        Reads the provided transactions, derives fresh sub_category
        and category values from description text, and identifies
        rows where the categorization has changed.

        Args:
            transactions: DataFrame with at least ``description``,
                ``sub_category``, and ``category`` columns.

        Returns:
            Tuple of (updated_df, result) where updated_df contains
            only the rows whose categorization changed, with new
            sub_category and category values applied.

        Example:
            >>> result_df, result = service.recategorize(
            ...     transactions=all_txns,
            ... )
            >>> result.updated_count
            5
        """
        if transactions.empty:
            return pd.DataFrame(), RecategorizeResult(
                success=True,
                message="No transactions to recategorize",
                total_transactions=0,
                updated_count=0,
            )

        df = transactions.copy()
        total = len(df)

        new_sub = df["description"].astype(str).map(
            lambda desc: map_by_keywords_substring(
                desc, self._mappers.description_to_sub_category,
            ),
        )
        new_cat = new_sub.astype(str).map(
            lambda sub: map_by_keywords_exact(
                sub, self._mappers.sub_category_to_category,
            ),
        )

        changed_mask = (
            (df["sub_category"].fillna("") != new_sub.fillna(""))
            | (df["category"].fillna("") != new_cat.fillna(""))
        )

        df["sub_category"] = new_sub
        df["category"] = new_cat

        updated_df = df[changed_mask].copy()
        updated_count = len(updated_df)

        self._logger.info(
            "Recategorized %d / %d transactions",
            updated_count, total,
        )

        return updated_df, RecategorizeResult(
            success=True,
            message=(
                f"Updated {updated_count} of "
                f"{total} transactions"
            ),
            total_transactions=total,
            updated_count=updated_count,
        )


class RecategorizeOrchestrator:
    """Orchestrator that coordinates transaction re-categorization.

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
        """Initialize the recategorize orchestrator.

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
            >>> result = orchestrator.run()
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


# Backward-compat alias
RecategorizeController = RecategorizeOrchestrator
