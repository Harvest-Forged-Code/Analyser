"""Expenses router for Budget Analyser API.

Provides endpoints for expense statistics and transaction details.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, Query, HTTPException

from budget_analyser.api.dependencies import get_expenses_stats_controller
from budget_analyser.features.reporting.expenses_service import (
    ExpensesStatsService,
)

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


def _df_to_records(df: pd.DataFrame | None) -> list[dict[str, Any]]:
    """Convert DataFrame to list of dicts with date serialization.

    Args:
        df: Input DataFrame.

    Returns:
        List of record dictionaries with ISO date strings.
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return []
    result = df.copy()
    for col in result.columns:
        if pd.api.types.is_datetime64_any_dtype(result[col]):
            result[col] = result[col].dt.strftime("%Y-%m-%d")
        elif hasattr(result[col].dtype, 'freq'):
            # Convert Period columns (e.g. year_month) to strings
            result[col] = result[col].astype(str)
    return result.to_dict(orient="records")


@router.get("/months")
def get_available_months(
    *, controller: ExpensesStatsService = Depends(
        get_expenses_stats_controller,
    ),
) -> list[str]:
    """List all available months with expense data.

    Args:
        controller: Injected ExpensesStatsService.

    Returns:
        List of month strings (e.g., "2024-01").
    """
    return [str(p) for p in controller.available_months()]


@router.get("/month/{period}")
def get_month_category_breakdown(
    *,
    period: str,
    controller: ExpensesStatsService = Depends(
        get_expenses_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get expense category breakdown for a specific month.

    Args:
        period: Month period string (e.g., "2024-01").
        controller: Injected ExpensesStatsService.

    Returns:
        List of category breakdown records.

    Raises:
        HTTPException: If period is invalid or data not found.
    """
    try:
        period_obj = pd.Period(period)
        breakdown = controller.category_breakdown(period_obj)
        result = []
        for cat_name, _cat_total, subcats in breakdown:
            for sub_name, amount in subcats:
                result.append({
                    "category": cat_name,
                    "sub_category": sub_name,
                    "amount": amount,
                })
        return result
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=404, detail=f"Invalid period or data not found: {e}",
        ) from e


@router.get("/month/{period}/transactions")
def get_month_transactions(
    *,
    period: str,
    category: str | None = Query(None),
    sub_category: str | None = Query(None),
    controller: ExpensesStatsService = Depends(
        get_expenses_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get transactions for a specific month.

    Args:
        period: Month period string (e.g., "2024-01").
        category: Optional category filter.
        sub_category: Optional sub-category filter.
        controller: Injected ExpensesStatsService.

    Returns:
        List of transaction records.

    Raises:
        HTTPException: If period is invalid or data not found.
    """
    try:
        period_obj = pd.Period(period)
        df = controller.transactions(
            period_obj, category=category, sub_category=sub_category,
        )
        return _df_to_records(df)
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=404, detail=f"Invalid period or data not found: {e}",
        ) from e


@router.get("/year/{year}")
def get_year_table(
    *,
    year: int,
    controller: ExpensesStatsService = Depends(
        get_expenses_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get expense table for a full year.

    Args:
        year: Year as integer.
        controller: Injected ExpensesStatsService.

    Returns:
        List of monthly expense records.

    Raises:
        HTTPException: If year is invalid or data not found.
    """
    try:
        total = controller.total_for_year(year)
        return [{"year": year, "total": total}]
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=404, detail=f"Invalid year or data not found: {e}",
        ) from e


@router.get("/year/{year}/breakdown")
def get_year_breakdown(
    *,
    year: int,
    controller: ExpensesStatsService = Depends(
        get_expenses_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get category breakdown for a year.

    Args:
        year: Year as integer.
        controller: Injected ExpensesStatsService.

    Returns:
        List of category breakdown records.

    Raises:
        HTTPException: If year is invalid or data not found.
    """
    try:
        breakdown = controller.year_breakdown(year)
        result = []
        for period, total, categories in breakdown:
            row: dict[str, Any] = {"month": str(period), "total": total}
            for cat_name, cat_total, _ in categories:
                row[cat_name] = cat_total
            result.append(row)
        return result
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=404, detail=f"Invalid year or data not found: {e}",
        ) from e


@router.get("/year/{year}/transactions")
def get_year_transactions(
    *,
    year: int,
    month: int | None = Query(None),
    category: str | None = Query(None),
    sub_category: str | None = Query(None),
    controller: ExpensesStatsService = Depends(
        get_expenses_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get transactions for a full year with optional filters.

    Args:
        year: Year as integer.
        month: Optional month filter (1-12).
        category: Optional category filter.
        sub_category: Optional sub-category filter.
        controller: Injected ExpensesStatsService.

    Returns:
        List of transaction records.

    Raises:
        HTTPException: If year is invalid or data not found.
    """
    try:
        df = controller.transactions_for_year(
            year,
            month=month,
            category=category,
            sub_category=sub_category,
        )
        return _df_to_records(df)
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=404, detail=f"Invalid year or data not found: {e}",
        ) from e


@router.get("/range")
def get_range_table(
    *,
    start_date: str = Query(...),
    end_date: str = Query(...),
    controller: ExpensesStatsService = Depends(
        get_expenses_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get expense table for a custom date range.

    Args:
        start_date: Start date in ISO format (YYYY-MM-DD).
        end_date: End date in ISO format (YYYY-MM-DD).
        controller: Injected ExpensesStatsService.

    Returns:
        List of expense records.

    Raises:
        HTTPException: If dates are invalid or data not found.
    """
    try:
        df = controller.table_for_range(start_date, end_date)
        return _df_to_records(df)
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=404, detail=f"Invalid date range or data not found: {e}",
        ) from e
