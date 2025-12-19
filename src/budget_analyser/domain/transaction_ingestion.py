"""Transaction ingestion service (domain logic).

Purpose:
    Process uploaded CSV files and save categorized transactions to the database.

Goal:
    Provide a single entry point for ingesting bank statements into the system,
    handling formatting, categorization, and persistence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd

from budget_analyser.domain.statement_formatter import create_statement_formatter
from budget_analyser.domain.transaction_processing import CategoryMappers, TransactionProcessor
from budget_analyser.infrastructure.database import TransactionDatabase


@dataclass
class IngestionResult:
    """Result of a transaction ingestion operation."""

    success: bool
    message: str
    transactions_processed: int = 0
    transactions_inserted: int = 0
    duplicates_skipped: int = 0


class TransactionIngestionService:
    """Service to ingest bank statement CSVs into the database.

    Responsibilities:
        - Load and format CSV files using appropriate statement formatter
        - Categorize transactions using keyword mappings
        - Insert processed transactions into the database (no duplicates)
    """

    def __init__(
        self,
        *,
        database: TransactionDatabase,
        category_mappers: CategoryMappers,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the ingestion service.

        Args:
            database: TransactionDatabase instance for persistence.
            category_mappers: Mappers for transaction categorization.
            logger: Optional logger for diagnostics.
        """
        self._database = database
        self._category_mappers = category_mappers
        self._logger = logger or logging.getLogger("budget_analyser.ingestion")

    def ingest_csv(
        self,
        csv_path: Path,
        account_name: str,
        column_mapping: Mapping[str, str],
    ) -> IngestionResult:
        """Ingest a single CSV file into the database.

        Args:
            csv_path: Path to the CSV file.
            account_name: Account identifier (e.g., "citi", "chase").
            column_mapping: Mapping from source columns to canonical names.

        Returns:
            IngestionResult with success status and statistics.
        """
        try:
            # Step 1: Load CSV
            self._logger.info("Loading CSV: %s for account: %s", csv_path, account_name)
            raw_df = pd.read_csv(csv_path)

            if raw_df.empty:
                return IngestionResult(
                    success=False,
                    message="CSV file is empty",
                )

            # Step 2: Format using statement formatter
            self._logger.info("Formatting %d rows for account: %s", len(raw_df), account_name)
            formatter = create_statement_formatter(
                account_name=account_name,
                statement=raw_df,
                column_mapping=column_mapping,
            )
            formatted_df = formatter.get_desired_format()

            # Step 3: Categorize transactions
            self._logger.info("Categorizing transactions for account: %s", account_name)
            processor = TransactionProcessor(mappers=self._category_mappers)
            processed_df = processor.process(raw_transactions=formatted_df)

            # Step 4: Insert into database
            self._logger.info("Inserting %d transactions into database", len(processed_df))
            inserted_count = self._database.insert_transactions(processed_df)
            duplicates = len(processed_df) - inserted_count

            self._logger.info(
                "Ingestion complete: %d processed, %d inserted, %d duplicates skipped",
                len(processed_df),
                inserted_count,
                duplicates,
            )

            return IngestionResult(
                success=True,
                message=f"Successfully processed {len(processed_df)} transactions",
                transactions_processed=len(processed_df),
                transactions_inserted=inserted_count,
                duplicates_skipped=duplicates,
            )

        except FileNotFoundError:
            msg = f"CSV file not found: {csv_path}"
            self._logger.error(msg)
            return IngestionResult(success=False, message=msg)

        except Exception as exc:  # pylint: disable=broad-exception-caught
            msg = f"Failed to ingest CSV: {exc}"
            self._logger.exception(msg)
            return IngestionResult(success=False, message=msg)

    def ingest_multiple_csvs(
        self,
        csv_files: list[tuple[Path, str, Mapping[str, str]]],
    ) -> IngestionResult:
        """Ingest multiple CSV files into the database.

        Args:
            csv_files: List of tuples (csv_path, account_name, column_mapping).

        Returns:
            Aggregated IngestionResult with combined statistics.
        """
        total_processed = 0
        total_inserted = 0
        total_duplicates = 0
        errors: list[str] = []

        for csv_path, account_name, column_mapping in csv_files:
            result = self.ingest_csv(csv_path, account_name, column_mapping)
            if result.success:
                total_processed += result.transactions_processed
                total_inserted += result.transactions_inserted
                total_duplicates += result.duplicates_skipped
            else:
                errors.append(f"{account_name}: {result.message}")

        if errors:
            return IngestionResult(
                success=False,
                message=f"Some files failed: {'; '.join(errors)}",
                transactions_processed=total_processed,
                transactions_inserted=total_inserted,
                duplicates_skipped=total_duplicates,
            )

        return IngestionResult(
            success=True,
            message=f"Successfully ingested {len(csv_files)} files",
            transactions_processed=total_processed,
            transactions_inserted=total_inserted,
            duplicates_skipped=total_duplicates,
        )
