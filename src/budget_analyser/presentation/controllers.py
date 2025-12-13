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
    month: pd.Period
    earnings: pd.DataFrame
    expenses: pd.DataFrame
    expenses_category: pd.DataFrame
    expenses_sub_category: pd.DataFrame


class BackendController:
    def __init__(
        self,
        *,
        statement_repository: StatementRepository,
        column_mappings: ColumnMappingProvider,
        category_mappings: CategoryMappingProvider,
        report_service: ReportService,
        logger: logging.Logger,
    ) -> None:
        self._statement_repository = statement_repository
        self._column_mappings = column_mappings
        self._category_mappings = category_mappings
        self._report_service = report_service
        self._logger = logger

    def run(self) -> list[MonthlyReports]:
        self._logger.info("Loading statements")
        statements = self._statement_repository.get_statements()

        formatted_frames: list[pd.DataFrame] = []
        for account, raw_statement in statements.items():
            column_mapping = self._column_mappings.get_column_mapping(account)
            formatter = create_statement_formatter(
                account_name=account,
                statement=raw_statement,
                column_mapping=column_mapping,
            )
            formatted_frames.append(formatter.get_desired_format())

        if not formatted_frames:
            return []

        transactions = pd.concat(formatted_frames, ignore_index=True)

        processor = TransactionProcessor(
            mappers=CategoryMappers(
                description_to_sub_category=self._category_mappings.description_to_sub_category(),
                sub_category_to_category=self._category_mappings.sub_category_to_category(),
            )
        )
        processed = processor.process(raw_transactions=transactions)
        processed["year_month"] = processed["transaction_date"].dt.to_period("M")

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

        return reports
