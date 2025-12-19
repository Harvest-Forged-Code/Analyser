"""Backend controller (presentation layer orchestration).

Single responsibility:
    Orchestrate the end-to-end workflow: load statements -> format -> process -> report.
"""

from __future__ import annotations

import logging
from typing import List
import time

import pandas as pd

from budget_analyser.domain.protocols import (
    CategoryMappingProvider,
    ColumnMappingProvider,
    StatementRepository,
)
from budget_analyser.domain.reporting import ReportService
from budget_analyser.domain.statement_formatter import create_statement_formatter
from budget_analyser.domain.transaction_processing import CategoryMappers, TransactionProcessor
from budget_analyser.controller.monthly_reports import MonthlyReports


class BackendController:  # pylint: disable=too-few-public-methods
    """Controller that runs the backend reporting workflow."""

    def __init__(
        self,
        *,
        statement_repository: StatementRepository,
        column_mappings: ColumnMappingProvider,
        category_mappings: CategoryMappingProvider,
        report_service: ReportService,
        logger: logging.Logger,
    ) -> None:
        """Create the controller.

        Args:
            statement_repository: Loads raw statements (infrastructure).
            column_mappings: Provides per-account column mapping (infrastructure).
            category_mappings: Provides keyword mappers (infrastructure).
            report_service: Domain service to build reports.
            logger: Logger used for operational logs.
        """
        # Store dependencies (constructor injection).
        self._statement_repository = statement_repository
        self._column_mappings = column_mappings
        self._category_mappings = category_mappings
        self._report_service = report_service
        self._logger = logger

    def run(self) -> List[MonthlyReports]:  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """Execute the workflow and return month-wise report tables.

        Returns:
            A list of `MonthlyReports` objects (one per month).
        """
        # 1) Load raw statement data.
        t0 = time.perf_counter()
        self._logger.info("Loading statements")
        statements = self._statement_repository.get_statements()
        self._logger.info("Pipeline start: accounts=%d", len(statements))

        # 2) Format each statement using account-specific column mapping.
        formatted_frames: list[pd.DataFrame] = []
        for account, raw_statement in statements.items():
            try:
                # Per-account diagnostics before formatting
                try:
                    shape = getattr(raw_statement, "shape", None)
                    cols = list(getattr(raw_statement, "columns", []))
                    self._logger.debug(
                        "Formatting account=%s raw_shape=%s raw_cols=%s",
                        account,
                        shape,
                        cols,
                    )
                except Exception:  # pylint: disable=broad-exception-caught
                    pass

                # Load mapping and choose a formatter.
                column_mapping = self._column_mappings.get_column_mapping(account)
                try:
                    self._logger.debug(
                        "Account=%s column_mapping size=%d sample_keys=%s",
                        account,
                        len(column_mapping or {}),
                        list((column_mapping or {}).keys())[:5],
                    )
                except Exception:  # pylint: disable=broad-exception-caught
                    pass

                formatter = create_statement_formatter(
                    account_name=account,
                    statement=raw_statement,
                    column_mapping=column_mapping,
                )
                # Normalize to canonical schema.
                formatted = formatter.get_desired_format()
                try:
                    self._logger.debug(
                        "Formatted account=%s shape=%s cols=%s",
                        account,
                        getattr(formatted, "shape", None),
                        list(getattr(formatted, "columns", [])),
                    )
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
                formatted_frames.append(formatted)
            except Exception:  # pylint: disable=broad-exception-caught
                # Log rich context and re-raise
                try:
                    head_repr = None
                    try:
                        head_repr = raw_statement.head(5).to_dict()  # type: ignore[assignment]
                    except Exception:  # pylint: disable=broad-exception-caught
                        fallback = getattr(raw_statement, "head", lambda n=5, rs=raw_statement: rs)
                        head_repr = str(fallback())[:500]
                    mapping_keys = (
                        list((column_mapping or {}).keys())[:10]
                        if 'column_mapping' in locals() else []
                    )
                    self._logger.exception(
                        "Formatting failed for account=%s; cols=%s; mapping_keys=%s; head=%s",
                        account,
                        list(getattr(raw_statement, "columns", [])),
                        mapping_keys,
                        head_repr,
                    )
                except Exception:  # pylint: disable=broad-exception-caught
                    self._logger.exception("Formatting failed for account=%s", account)
                raise

        # Fast-exit when there is no data.
        if not formatted_frames:
            return []

        # 3) Merge all formatted statements.
        transactions = pd.concat(formatted_frames, ignore_index=True)
        try:
            self._logger.debug(
                "Merged transactions shape=%s cols=%s",
                transactions.shape,
                list(transactions.columns),
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        # 4) Categorize using JSON keyword mappings.
        processor = TransactionProcessor(
            mappers=CategoryMappers(
                description_to_sub_category=self._category_mappings.description_to_sub_category(),
                sub_category_to_category=self._category_mappings.sub_category_to_category(),
            )
        )
        processed = processor.process(raw_transactions=transactions)

        # 5) Add a month period column for grouping.
        processed["year_month"] = processed["transaction_date"].dt.to_period("M")

        # 6) Build month-wise report tables.
        reports: list[MonthlyReports] = []
        for month, group in processed.groupby(processed["year_month"]):
            self._logger.info("Generating reports for %s", month)
            # Exclusion rules for standard reports:
            # - Do not include payment confirmations as earnings
            # - Do not include payments made as expenses
            # Keep full group for specialized pages (e.g., reconciliation)
            try:
                earn_source = group
                exp_source = group
                if "sub_category" in group.columns:
                    earn_source = group[group["sub_category"].fillna("") != "payment_confirmations"]
                    exp_source = group[group["sub_category"].fillna("") != "payments_made"]
                else:
                    self._logger.debug(
                        "No sub_category column present for %s; "
                        "skipping payments exclusions in aggregates",
                        month,
                    )
            except Exception:  # pylint: disable=broad-exception-caught
                earn_source = group
                exp_source = group

            reports.append(
                MonthlyReports(
                    month=month,
                    earnings=self._report_service.earnings(statement=earn_source),
                    expenses=self._report_service.expenses(statement=exp_source),
                    expenses_category=self._report_service.expenses_category(statement=exp_source),
                    expenses_sub_category=self._report_service.expenses_sub_category(
                        statement=exp_source
                    ),
                    transactions=group,
                )
            )

        # Return computed reports.
        try:
            duration = time.perf_counter() - t0
            months = processed["year_month"].nunique()
            self._logger.info(
                "Pipeline end: transactions=%d months=%d duration=%.2fs",
                len(processed.index),
                int(months),
                duration,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        return reports

    def run_from_database(self, processed_transactions: pd.DataFrame) -> List[MonthlyReports]:
        """Generate reports from pre-processed database transactions.

        This method skips the CSV loading, formatting, and categorization steps
        since the database already contains processed transactions.

        Args:
            processed_transactions: DataFrame with columns: transaction_date,
                description, amount, from_account, sub_category, category, c_or_d

        Returns:
            A list of `MonthlyReports` objects (one per month).
        """
        t0 = time.perf_counter()
        tx_count = len(processed_transactions)
        self._logger.info("Generating reports from database: %d transactions", tx_count)

        if processed_transactions.empty:
            self._logger.info("No transactions in database")
            return []

        # Ensure transaction_date is datetime
        if "transaction_date" in processed_transactions.columns:
            processed_transactions["transaction_date"] = pd.to_datetime(
                processed_transactions["transaction_date"], format="mixed", errors="coerce"
            )

        # Add year_month period column for grouping
        date_col = processed_transactions["transaction_date"]
        processed_transactions["year_month"] = date_col.dt.to_period("M")

        # Build month-wise report tables (same logic as run())
        reports: list[MonthlyReports] = []
        for month, group in processed_transactions.groupby(processed_transactions["year_month"]):
            self._logger.info("Generating reports for %s", month)
            try:
                earn_source = group
                exp_source = group
                if "sub_category" in group.columns:
                    earn_source = group[group["sub_category"].fillna("") != "payment_confirmations"]
                    exp_source = group[group["sub_category"].fillna("") != "payments_made"]
            except Exception:  # pylint: disable=broad-exception-caught
                earn_source = group
                exp_source = group

            reports.append(
                MonthlyReports(
                    month=month,
                    earnings=self._report_service.earnings(statement=earn_source),
                    expenses=self._report_service.expenses(statement=exp_source),
                    expenses_category=self._report_service.expenses_category(statement=exp_source),
                    expenses_sub_category=self._report_service.expenses_sub_category(
                        statement=exp_source
                    ),
                    transactions=group,
                )
            )

        try:
            duration = time.perf_counter() - t0
            months = processed_transactions["year_month"].nunique()
            self._logger.info(
                "Database pipeline end: transactions=%d months=%d duration=%.2fs",
                len(processed_transactions.index),
                int(months),
                duration,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        return reports
