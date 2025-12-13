"""Presentation controllers.

Purpose:
    Orchestrate the end-to-end workflow: load statements -> format -> process -> report.

Goal:
    Keep IO out of the controller and delegate business rules to domain services.

Steps:
    1. Load raw statements via repository.
    2. Normalize statements via formatter.
    3. Merge and categorize transactions.
    4. Group by month and build report tables.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

import logging
from dataclasses import dataclass

import pandas as pd

from budget_analyser.domain.protocols import (
    CategoryMappingProvider,
    ColumnMappingProvider,
    StatementRepository,
)
from budget_analyser.domain.reporting import ReportService
from budget_analyser.domain.statement_formatter import create_statement_formatter
from budget_analyser.domain.transaction_processing import CategoryMappers, TransactionProcessor


@dataclass(frozen=True)
class MonthlyReports:
    """Report tables for a single month."""

    month: pd.Period
    earnings: pd.DataFrame
    expenses: pd.DataFrame
    expenses_category: pd.DataFrame
    expenses_sub_category: pd.DataFrame


class BackendController:
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

    def run(self) -> list[MonthlyReports]:
        """Execute the workflow and return month-wise report tables.

        Steps:
            1. Load raw statements.
            2. Format each statement into canonical schema.
            3. Concatenate into a single transactions table.
            4. Categorize and enrich transactions.
            5. Group by month and compute report pivots.

        Returns:
            A list of `MonthlyReports` objects (one per month).
        """
        # 1) Load raw statement data.
        self._logger.info("Loading statements")
        statements = self._statement_repository.get_statements()

        # 2) Format each statement using account-specific column mapping.
        formatted_frames: list[pd.DataFrame] = []
        for account, raw_statement in statements.items():
            # Load mapping and choose a formatter.
            column_mapping = self._column_mappings.get_column_mapping(account)
            formatter = create_statement_formatter(
                account_name=account,
                statement=raw_statement,
                column_mapping=column_mapping,
            )
            # Normalize to canonical schema.
            formatted_frames.append(formatter.get_desired_format())

        # Fast-exit when there is no data.
        if not formatted_frames:
            return []

        # 3) Merge all formatted statements.
        transactions = pd.concat(formatted_frames, ignore_index=True)

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
            reports.append(
                MonthlyReports(
                    month=month,
                    earnings=self._report_service.earnings(statement=group),
                    expenses=self._report_service.expenses(statement=group),
                    expenses_category=self._report_service.expenses_category(statement=group),
                    expenses_sub_category=self._report_service.expenses_sub_category(
                        statement=group
                    ),
                )
            )

        # Return computed reports.
        return reports
