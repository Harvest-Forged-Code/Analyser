"""Export router for Budget Analyser API.

Provides endpoints for exporting transactions and summaries to CSV and PDF.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, Query

from budget_analyser.api.dependencies import get_reports
from budget_analyser.core.models import MonthlyReports
from budget_analyser.features.export.service import ExportService

router = APIRouter(prefix="/api/export", tags=["export"])


def _all_transactions_df(reports: list[MonthlyReports]) -> pd.DataFrame:
    """Concatenate all transactions from reports.

    Args:
        reports: List of MonthlyReports to extract transactions from.

    Returns:
        Combined DataFrame of all transactions, or empty DataFrame.
    """
    frames = []
    for r in reports:
        if r.transactions is not None and not r.transactions.empty:
            frames.append(r.transactions)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _all_expenses_df(reports: list[MonthlyReports]) -> pd.DataFrame:
    """Concatenate all expenses DataFrames from reports.

    Args:
        reports: List of MonthlyReports to extract expenses from.

    Returns:
        Combined DataFrame of all expenses, or empty DataFrame.
    """
    frames = []
    for r in reports:
        if r.expenses is not None and not r.expenses.empty:
            frames.append(r.expenses)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@router.post("/transactions/csv")
def export_transactions_csv(
    *,
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    category: str | None = Query(None),
    reports: list[MonthlyReports] = Depends(get_reports),
) -> dict[str, str]:
    """Export transactions to CSV file.

    Args:
        start_date: Optional start date filter (ISO format).
        end_date: Optional end date filter (ISO format).
        category: Optional category filter.
        reports: Injected reports cache.

    Returns:
        Dict with file path to the exported CSV.
    """
    transactions_df = _all_transactions_df(reports)

    # Apply filters
    filtered_df = transactions_df.copy()
    if start_date:
        filtered_df = filtered_df[
            filtered_df["transaction_date"] >= pd.to_datetime(start_date)
        ]
    if end_date:
        filtered_df = filtered_df[
            filtered_df["transaction_date"] <= pd.to_datetime(end_date)
        ]
    if category:
        filtered_df = filtered_df[filtered_df["category"] == category]

    # Convert to list of dicts
    transactions_list = filtered_df.to_dict(orient="records")

    # Create temp file
    temp_dir = Path(tempfile.gettempdir())
    output_path = temp_dir / "transactions_export.csv"

    service = ExportService()
    service.export_transactions_csv(
        transactions=transactions_list,
        filepath=output_path,
    )

    return {"file_path": str(output_path)}


@router.post("/transactions/pdf")
def export_transactions_pdf(
    *,
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    category: str | None = Query(None),
    title: str = Query("Transaction Report"),
    reports: list[MonthlyReports] = Depends(get_reports),
) -> dict[str, str]:
    """Export transactions to PDF file.

    Args:
        start_date: Optional start date filter (ISO format).
        end_date: Optional end date filter (ISO format).
        category: Optional category filter.
        title: Report title.
        reports: Injected reports cache.

    Returns:
        Dict with file path to the exported PDF.
    """
    transactions_df = _all_transactions_df(reports)

    # Apply filters
    filtered_df = transactions_df.copy()
    if start_date:
        filtered_df = filtered_df[
            filtered_df["transaction_date"] >= pd.to_datetime(start_date)
        ]
    if end_date:
        filtered_df = filtered_df[
            filtered_df["transaction_date"] <= pd.to_datetime(end_date)
        ]
    if category:
        filtered_df = filtered_df[filtered_df["category"] == category]

    # Convert to list of dicts
    transactions_list = filtered_df.to_dict(orient="records")

    # Create temp file
    temp_dir = Path(tempfile.gettempdir())
    output_path = temp_dir / "transactions_export.pdf"

    service = ExportService()
    service.export_transactions_pdf(
        transactions=transactions_list,
        filepath=output_path,
        config={"title": title},
    )

    return {"file_path": str(output_path)}


@router.post("/summary/csv")
def export_summary_csv(
    *,
    year: int | None = Query(None),
    reports: list[MonthlyReports] = Depends(get_reports),
) -> dict[str, str]:
    """Export expense summary to CSV file.

    Args:
        year: Optional year filter.
        reports: Injected reports cache.

    Returns:
        Dict with file path to the exported CSV.
    """
    # Filter reports by year if specified
    filtered_reports = reports
    if year is not None:
        filtered_reports = [r for r in reports if r.month.year == year]

    expenses_df = _all_expenses_df(filtered_reports)

    # Group by category for summary
    if not expenses_df.empty:
        summary_df = expenses_df.groupby("category").agg(
            total=("amount", "sum"),
            count=("amount", "count"),
            average=("amount", "mean"),
        ).reset_index()
        summary_list = summary_df.to_dict(orient="records")
    else:
        summary_list = []

    # Create temp file
    temp_dir = Path(tempfile.gettempdir())
    output_path = temp_dir / "summary_export.csv"

    service = ExportService()
    service.export_transactions_csv(
        transactions=summary_list,
        filepath=output_path,
        columns=service.SUMMARY_COLUMNS,
    )

    return {"file_path": str(output_path)}
