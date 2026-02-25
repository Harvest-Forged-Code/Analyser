"""Report service (business logic).

Provides pure functions/use-cases that generate report tables
from processed transaction data, and the end-to-end report
pipeline orchestrator.
"""

from __future__ import annotations

import logging
import time
from typing import Mapping

import pandas as pd

from budget_analyser.core.models import MonthlyReports
from budget_analyser.core.protocols import (
    CategoryMappingProvider,
    ColumnMappingProvider,
    StatementRepository,
)
from budget_analyser.features.ingestion.categorization import (
    CategoryMappers,
    TransactionProcessor,
)
from budget_analyser.features.ingestion.formatters import (
    create_statement_formatter,
)


class ReportService:
    """Service that creates report DataFrames from transactions."""

    def __init__(
        self,
        *,
        cashflow_mapping: Mapping[str, list[str]],
    ) -> None:
        """Initialize the report service from the cashflow JSON mapping.

        Category sets are derived entirely from the provided mapping —
        no hardcoded defaults exist. The mapping must contain at least
        an ``"earnings"`` key or an ``"expenses"`` key.

        Args:
            cashflow_mapping: Mapping with ``"earnings"`` and
                ``"expenses"`` keys pointing to category lists
                (loaded from ``cashflow_to_category.json``).

        Raises:
            ValueError: If the mapping is empty or yields no usable
                category sets.

        Example:
            >>> svc = ReportService(
            ...     cashflow_mapping={
            ...         "Earnings": ["Primary_Income", "Refunded_money"],
            ...         "Expenses": ["Needs", "Luxury"],
            ...     },
            ... )
        """
        if not cashflow_mapping:
            raise ValueError(
                "cashflow_mapping is required and must not be empty. "
                "Check cashflow_to_category.json."
            )

        earnings = self._lookup_flow(cashflow_mapping, "earnings")
        expenses = self._lookup_flow(cashflow_mapping, "expenses")

        earnings_categories: set[str] = (
            {str(c).strip() for c in earnings if str(c).strip()}
            if earnings else set()
        )
        expense_categories: set[str] = (
            {str(c).strip() for c in expenses if str(c).strip()}
            if expenses else set()
        )

        if not earnings_categories and not expense_categories:
            raise ValueError(
                "cashflow_mapping must define at least one of "
                "'Earnings' or 'Expenses' category lists."
            )

        self._earnings_categories = earnings_categories
        self._expense_categories = expense_categories

    @staticmethod
    def _lookup_flow(
        mapping: Mapping[str, list[str]],
        key: str,
    ) -> list[str] | None:
        """Look up a cashflow mapping key case-insensitively.

        Iterates the mapping entries and returns the value whose
        key matches *key* (lowercased comparison).

        Args:
            mapping: Cashflow category mapping to search.
            key: The key to look up (e.g. ``"earnings"``).

        Returns:
            The category list if found, or ``None``
            when no matching key exists.

        Example:
            >>> ReportService._lookup_flow(
            ...     {"Earnings": ["Income"]}, "earnings",
            ... )
            ['Income']
        """
        for k, v in mapping.items():
            try:
                if str(k).lower() == key:
                    return list(v)
            except (TypeError, AttributeError, ValueError):
                continue
        return None

    def earnings(
        self, *, statement: pd.DataFrame,
    ) -> pd.DataFrame:
        """Return earnings restricted to configured categories.

        Filters the statement to rows whose category is in the
        earnings set and whose amount is positive. Amounts are
        converted to their absolute value.

        Args:
            statement: Processed transaction DataFrame with at
                least an ``"amount"`` column and optionally a
                ``"category"`` column.

        Returns:
            DataFrame of earnings transactions with positive
            absolute amounts.

        Example:
            >>> import pandas as pd
            >>> svc = ReportService()
            >>> df = pd.DataFrame({
            ...     "amount": [1000, -50],
            ...     "category": ["Primary_Income", "Needs"],
            ... })
            >>> result = svc.earnings(statement=df)
            >>> len(result)
            1
        """
        if "category" in statement.columns:
            mask = statement["category"].fillna("").isin(
                self._earnings_categories,
            )
            amount_mask = statement["amount"] > 0
            df = statement[mask & amount_mask].copy()
        else:
            df = statement[statement["amount"] > 0].copy()

        if not df.empty:
            df["amount"] = df["amount"].abs()
        return df

    def expenses(
        self, *, statement: pd.DataFrame,
    ) -> pd.DataFrame:
        """Return expenses including refunds as reductions.

        Filters the statement to rows that belong to expense
        categories. Refunded amounts are kept positive to act
        as reductions; all other expense amounts are negated.

        Args:
            statement: Processed transaction DataFrame with at
                least an ``"amount"`` column and optionally a
                ``"category"`` column.

        Returns:
            DataFrame of expense transactions where non-refund
            amounts are negative and refund amounts are positive.

        Example:
            >>> import pandas as pd
            >>> svc = ReportService()
            >>> df = pd.DataFrame({
            ...     "amount": [-200, 50],
            ...     "category": ["Needs", "Refunded_money"],
            ... })
            >>> result = svc.expenses(statement=df)
            >>> len(result)
            2
        """
        if "category" in statement.columns:
            categories = statement["category"].fillna("")
            negative_mask = statement["amount"] < 0
            expense_mask = categories.isin(
                self._expense_categories
                - self._earnings_categories,
            )
            df = statement[
                negative_mask | expense_mask
            ].copy()
            if not df.empty:
                df["amount"] = -df["amount"].abs()
            return df

        df = statement[statement["amount"] < 0].copy()
        if not df.empty:
            df["amount"] = -df["amount"].abs()
        return df

    def expenses_category(
        self, *, statement: pd.DataFrame,
    ) -> pd.DataFrame:
        """Return pivot table of expenses by category and month.

        Aggregates expense amounts by category (rows) and
        year-month (columns) with margin totals.

        Args:
            statement: Processed transaction DataFrame with
                ``"category"``, ``"year_month"``, and ``"amount"``
                columns.

        Returns:
            Pivot table DataFrame with categories as rows,
            months as columns, and a ``"Total"`` margin.

        Example:
            >>> import pandas as pd
            >>> svc = ReportService()
            >>> df = pd.DataFrame({
            ...     "amount": [-100, -200],
            ...     "category": ["Needs", "Needs"],
            ...     "year_month": ["2024-01", "2024-02"],
            ... })
            >>> pivot = svc.expenses_category(statement=df)
            >>> "Total" in pivot.columns
            True
        """
        expenses = self.expenses(statement=statement)
        return expenses.pivot_table(
            index="category",
            columns="year_month",
            values="amount",
            aggfunc="sum",
            margins=True,
            margins_name="Total",
        )

    def expenses_sub_category(
        self, *, statement: pd.DataFrame,
    ) -> pd.DataFrame:
        """Return pivot table of expenses by sub-category and month.

        Aggregates expense amounts by sub-category (rows) and
        year-month (columns) with margin totals.

        Args:
            statement: Processed transaction DataFrame with
                ``"sub_category"``, ``"year_month"``, and
                ``"amount"`` columns.

        Returns:
            Pivot table DataFrame with sub-categories as rows,
            months as columns, and a ``"Total"`` margin.

        Example:
            >>> import pandas as pd
            >>> svc = ReportService()
            >>> df = pd.DataFrame({
            ...     "amount": [-50, -75],
            ...     "sub_category": ["Groceries", "Rent"],
            ...     "year_month": ["2024-01", "2024-01"],
            ... })
            >>> pivot = svc.expenses_sub_category(statement=df)
            >>> "Total" in pivot.columns
            True
        """
        expenses = self.expenses(statement=statement)
        return expenses.pivot_table(
            index="sub_category",
            columns="year_month",
            values="amount",
            aggfunc="sum",
            margins=True,
            margins_name="Total",
        )


class ReportPipelineService:  # pylint: disable=too-few-public-methods
    """Orchestrate the end-to-end reporting workflow.

    Loads statements, formats them, categorizes transactions, and
    generates month-wise report tables.
    """

    def __init__(
        self,
        *,
        statement_repository: StatementRepository,
        column_mappings: ColumnMappingProvider,
        category_mappings: CategoryMappingProvider,
        report_service: ReportService,
        logger: logging.Logger,
    ) -> None:
        """Create the pipeline service.

        Args:
            statement_repository: Loads raw statements.
            column_mappings: Provides per-account column mapping.
            category_mappings: Provides keyword mappers.
            report_service: Domain service to build reports.
            logger: Logger used for operational logs.
        """
        self._statement_repository = statement_repository
        self._column_mappings = column_mappings
        self._category_mappings = category_mappings
        self._report_service = report_service
        self._logger = logger

    def run(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        self,
    ) -> list[MonthlyReports]:
        """Execute the workflow and return month-wise report tables.

        Returns:
            A list of ``MonthlyReports`` objects (one per month).

        Raises:
            MappingNotFoundError: If column or category mappings are
                missing or misconfigured.
            DataSourceError: If statement CSV files cannot be read.
            ValidationError: If transaction data is malformed.
        """
        # 1) Load raw statement data.
        t0 = time.perf_counter()
        self._logger.info("Loading statements")
        statements = self._statement_repository.get_statements()
        self._logger.info(
            "Pipeline start: accounts=%d", len(statements),
        )

        # 2) Format each statement using account-specific column
        #    mapping.
        formatted_frames: list[pd.DataFrame] = []
        for account, raw_statement in statements.items():
            try:
                self._log_raw_diagnostics(account, raw_statement)
                column_mapping = (
                    self._column_mappings.get_column_mapping(account)
                )
                self._log_column_mapping(account, column_mapping)
                formatter = create_statement_formatter(
                    account_name=account,
                    statement=raw_statement,
                    column_mapping=column_mapping,
                )
                formatted = formatter.get_desired_format()
                self._log_formatted(account, formatted)
                formatted_frames.append(formatted)
            except Exception:  # pylint: disable=broad-exception-caught
                self._log_formatting_error(
                    account, raw_statement, locals(),
                )
                raise

        if not formatted_frames:
            return []

        # 3) Merge all formatted statements.
        transactions = pd.concat(
            formatted_frames, ignore_index=True,
        )
        self._log_debug_safe(
            "Merged transactions shape=%s cols=%s",
            transactions.shape,
            list(transactions.columns),
        )

        # 4) Categorize using JSON keyword mappings.
        processor = TransactionProcessor(
            mappers=CategoryMappers(
                description_to_sub_category=(
                    self._category_mappings
                    .description_to_sub_category()
                ),
                sub_category_to_category=(
                    self._category_mappings
                    .sub_category_to_category()
                ),
            )
        )
        processed = processor.process(raw_transactions=transactions)

        # 5) Add a month period column for grouping.
        processed["year_month"] = (
            processed["transaction_date"].dt.to_period("M")
        )

        # 6) Build month-wise report tables.
        reports = self._build_reports(processed)

        self._log_pipeline_summary(processed, t0)
        return reports

    def run_from_database(
        self, processed_transactions: pd.DataFrame,
    ) -> list[MonthlyReports]:
        """Generate reports from pre-processed database transactions.

        Skips the CSV loading, formatting, and categorization steps
        since the database already contains processed transactions.

        Args:
            processed_transactions: DataFrame with columns:
                transaction_date, description, amount,
                from_account, sub_category, category, c_or_d.

        Returns:
            A list of ``MonthlyReports`` objects (one per month).
        """
        t0 = time.perf_counter()
        tx_count = len(processed_transactions)
        self._logger.info(
            "Generating reports from database: %d transactions",
            tx_count,
        )

        if processed_transactions.empty:
            self._logger.info("No transactions in database")
            return []

        if "transaction_date" in processed_transactions.columns:
            processed_transactions["transaction_date"] = (
                pd.to_datetime(
                    processed_transactions["transaction_date"],
                    format="mixed",
                    errors="coerce",
                )
            )

        date_col = processed_transactions["transaction_date"]
        processed_transactions["year_month"] = (
            date_col.dt.to_period("M")
        )

        reports = self._build_reports(processed_transactions)

        self._log_pipeline_summary(
            processed_transactions, t0, prefix="Database pipeline",
        )
        return reports

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_reports(
        self, processed: pd.DataFrame,
    ) -> list[MonthlyReports]:
        """Build month-wise report tables from processed data."""
        reports: list[MonthlyReports] = []
        for month, group in processed.groupby(
            processed["year_month"],
        ):
            self._logger.info(
                "Generating reports for %s", month,
            )
            earn_source, exp_source = self._apply_exclusions(
                group, month,
            )
            reports.append(
                MonthlyReports(
                    month=month,
                    earnings=self._report_service.earnings(
                        statement=earn_source,
                    ),
                    expenses=self._report_service.expenses(
                        statement=exp_source,
                    ),
                    expenses_category=(
                        self._report_service.expenses_category(
                            statement=exp_source,
                        )
                    ),
                    expenses_sub_category=(
                        self._report_service.expenses_sub_category(
                            statement=exp_source,
                        )
                    ),
                    transactions=group,
                )
            )
        return reports

    def _apply_exclusions(
        self,
        group: pd.DataFrame,
        month: object,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Apply payment exclusion rules for standard reports."""
        try:
            earn_source = group
            exp_source = group
            if "sub_category" in group.columns:
                earn_source = group[
                    group["sub_category"].fillna("")
                    != "payment_confirmations"
                ]
                exp_source = group[
                    group["sub_category"].fillna("")
                    != "payments_made"
                ]
            else:
                self._logger.debug(
                    "No sub_category column for %s; "
                    "skipping payments exclusions",
                    month,
                )
        except Exception:  # pylint: disable=broad-exception-caught
            earn_source = group
            exp_source = group
        return earn_source, exp_source

    def _log_debug_safe(
        self, msg: str, *args: object,
    ) -> None:
        """Log a debug message, swallowing any errors."""
        try:
            self._logger.debug(msg, *args)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    def _log_raw_diagnostics(
        self, account: str, raw_statement: object,
    ) -> None:
        """Log shape and columns of the raw statement."""
        try:
            shape = getattr(raw_statement, "shape", None)
            cols = list(getattr(raw_statement, "columns", []))
            self._logger.debug(
                "Formatting account=%s raw_shape=%s "
                "raw_cols=%s",
                account, shape, cols,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    def _log_column_mapping(
        self,
        account: str,
        column_mapping: object,
    ) -> None:
        """Log column mapping metadata."""
        try:
            self._logger.debug(
                "Account=%s column_mapping size=%d "
                "sample_keys=%s",
                account,
                len(column_mapping or {}),  # type: ignore[arg-type]
                list(
                    (column_mapping or {}).keys()  # type: ignore[union-attr]
                )[:5],
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    def _log_formatted(
        self, account: str, formatted: object,
    ) -> None:
        """Log formatted statement metadata."""
        try:
            self._logger.debug(
                "Formatted account=%s shape=%s cols=%s",
                account,
                getattr(formatted, "shape", None),
                list(getattr(formatted, "columns", [])),
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    def _log_formatting_error(
        self,
        account: str,
        raw_statement: object,
        local_vars: dict[str, object],
    ) -> None:
        """Log rich context when formatting fails."""
        try:
            head_repr = None
            try:
                head_repr = raw_statement.head(5).to_dict()  # type: ignore[union-attr]
            except Exception:  # pylint: disable=broad-exception-caught
                fallback = getattr(
                    raw_statement, "head",
                    lambda n=5, rs=raw_statement: rs,
                )
                head_repr = str(fallback())[:500]
            column_mapping = local_vars.get("column_mapping")
            mapping_keys = (
                list(
                    (column_mapping or {}).keys()  # type: ignore[union-attr]
                )[:10]
                if column_mapping is not None else []
            )
            self._logger.exception(
                "Formatting failed for account=%s; "
                "cols=%s; mapping_keys=%s; head=%s",
                account,
                list(getattr(raw_statement, "columns", [])),
                mapping_keys,
                head_repr,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            self._logger.exception(
                "Formatting failed for account=%s", account,
            )

    def _log_pipeline_summary(
        self,
        processed: pd.DataFrame,
        t0: float,
        *,
        prefix: str = "Pipeline",
    ) -> None:
        """Log a final summary line for the pipeline run."""
        try:
            duration = time.perf_counter() - t0
            months = processed["year_month"].nunique()
            self._logger.info(
                "%s end: transactions=%d months=%d "
                "duration=%.2fs",
                prefix,
                len(processed.index),
                int(months),
                duration,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass


BackendController = ReportPipelineService  # backward compat
