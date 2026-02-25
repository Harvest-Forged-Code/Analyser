"""Earnings router for Budget Analyser API.

Provides endpoints for earnings statistics and transaction details.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, Query, HTTPException

from budget_analyser.api.dependencies import get_earnings_stats_controller
from budget_analyser.features.reporting.earnings_service import (
    EarningsStatsService,
)
from budget_analyser.features.reporting.models import (
    EarningsDashboard,
    EarningsMonthTrend,
    EarningsSourceTrend,
)

router = APIRouter(prefix="/api/earnings", tags=["earnings"])


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert DataFrame to list of dicts with date serialization.

    Args:
        df: Input DataFrame.

    Returns:
        List of record dictionaries with ISO date strings.
    """
    if df is None or df.empty:
        return []
    result = df.copy()
    for col in result.columns:
        if pd.api.types.is_datetime64_any_dtype(result[col]):
            result[col] = result[col].dt.strftime("%Y-%m-%d")
    return result.to_dict(orient="records")


@router.get("/months")
def get_available_months(
    *, controller: EarningsStatsService = Depends(
        get_earnings_stats_controller,
    ),
) -> list[str]:
    """List all available months with earnings data.

    Args:
        controller: Injected EarningsStatsService.

    Returns:
        List of month strings (e.g., "2024-01").
    """
    return [str(p) for p in controller.available_months()]


@router.get("/dashboard")
def get_dashboard(
    *,
    period: str = Query(...),
    controller: EarningsStatsService = Depends(
        get_earnings_stats_controller,
    ),
) -> dict[str, Any]:
    """Get aggregated earnings dashboard data for KPI cards.

    Args:
        period: Month period string (e.g., "2026-02").
        controller: Injected EarningsStatsService.

    Returns:
        EarningsDashboard fields as a dict.

    Raises:
        HTTPException: If period is invalid.
    """
    try:
        period_obj = pd.Period(period)
        dash: EarningsDashboard = controller.dashboard(period_obj)
        return {
            "current_month_total": dash.current_month_total,
            "previous_month_total": dash.previous_month_total,
            "mom_change_percent": dash.mom_change_percent,
            "ytd_total": dash.ytd_total,
            "goal_total": dash.goal_total,
            "goal_progress_percent": dash.goal_progress_percent,
            "period": dash.period,
            "year": dash.year,
            "sparkline": dash.sparkline,
        }
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Invalid period: {exc}",
        ) from exc


@router.get("/trend")
def get_trend(
    *,
    months: int = Query(12, ge=1, le=60),
    controller: EarningsStatsService = Depends(
        get_earnings_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get monthly earnings trend for chart data.

    Args:
        months: Number of recent months (default 12).
        controller: Injected EarningsStatsService.

    Returns:
        List of dicts with period, label, total.
    """
    items: list[EarningsMonthTrend] = controller.monthly_trend(
        months=months,
    )
    return [
        {
            "period": item.period,
            "label": item.label,
            "total": item.total,
        }
        for item in items
    ]


@router.get("/source-trend")
def get_source_trend(
    *,
    months: int = Query(6, ge=1, le=24),
    controller: EarningsStatsService = Depends(
        get_earnings_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get per-source monthly totals for sparklines.

    Args:
        months: Number of recent months (default 6).
        controller: Injected EarningsStatsService.

    Returns:
        List of dicts with sub_category and monthly data.
    """
    items: list[EarningsSourceTrend] = controller.source_trend(
        months=months,
    )
    return [
        {
            "sub_category": item.sub_category,
            "months": [
                {
                    "period": m.period,
                    "label": m.label,
                    "total": m.total,
                }
                for m in item.months
            ],
        }
        for item in items
    ]


@router.get("/month/{period}")
def get_month_table(
    *,
    period: str,
    controller: EarningsStatsService = Depends(
        get_earnings_stats_controller,
    ),
) -> dict[str, Any]:
    """Get earnings breakdown table for a specific month.

    Args:
        period: Month period string (e.g., "2024-01").
        controller: Injected EarningsStatsService.

    Returns:
        Dict with rows, actual_total, expected_total.

    Raises:
        HTTPException: If period is invalid or data not found.
    """
    try:
        period_obj = pd.Period(period)
        rows, actual_total, expected_total = controller.table_for_month(
            period_obj,
        )
        return {
            "rows": [
                {
                    "sub_category": row.sub_category,
                    "actual": row.actual,
                    "percent_of_total": row.percent_of_total,
                    "expected": row.expected,
                    "diff": row.diff,
                    "diff_percent": row.diff_percent,
                }
                for row in rows
            ],
            "actual_total": actual_total,
            "expected_total": expected_total,
        }
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=404, detail=f"Invalid period or data not found: {e}",
        ) from e


@router.get("/month/{period}/transactions")
def get_month_transactions(
    *,
    period: str,
    sub_category: str | None = Query(None),
    controller: EarningsStatsService = Depends(
        get_earnings_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get transactions for a specific month.

    Args:
        period: Month period string (e.g., "2024-01").
        sub_category: Optional sub-category filter.
        controller: Injected EarningsStatsService.

    Returns:
        List of transaction records.

    Raises:
        HTTPException: If period is invalid or data not found.
    """
    try:
        period_obj = pd.Period(period)
        df = controller.transactions(period_obj, sub_category=sub_category)
        return _df_to_records(df)
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=404, detail=f"Invalid period or data not found: {e}",
        ) from e


@router.get("/year/{year}")
def get_year_table(
    *,
    year: int,
    controller: EarningsStatsService = Depends(
        get_earnings_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get earnings table for a full year.

    Args:
        year: Year as integer.
        controller: Injected EarningsStatsService.

    Returns:
        List of monthly earnings records.

    Raises:
        HTTPException: If year is invalid or data not found.
    """
    try:
        df = controller.table_for_year(year)
        return _df_to_records(df)
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=404, detail=f"Invalid year or data not found: {e}",
        ) from e


@router.get("/year/{year}/breakdown")
def get_year_breakdown(
    *,
    year: int,
    controller: EarningsStatsService = Depends(
        get_earnings_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get sub-category breakdown for a year.

    Args:
        year: Year as integer.
        controller: Injected EarningsStatsService.

    Returns:
        List of sub-category breakdown records.

    Raises:
        HTTPException: If year is invalid or data not found.
    """
    try:
        df = controller.year_breakdown(year)
        return _df_to_records(df)
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=404, detail=f"Invalid year or data not found: {e}",
        ) from e


@router.get("/year/{year}/transactions")
def get_year_transactions(
    *,
    year: int,
    month: int | None = Query(None),
    sub_category: str | None = Query(None),
    controller: EarningsStatsService = Depends(
        get_earnings_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get transactions for a full year with optional filters.

    Args:
        year: Year as integer.
        month: Optional month filter (1-12).
        sub_category: Optional sub-category filter.
        controller: Injected EarningsStatsService.

    Returns:
        List of transaction records.

    Raises:
        HTTPException: If year is invalid or data not found.
    """
    try:
        df = controller.transactions_for_year(
            year, month=month, sub_category=sub_category,
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
    controller: EarningsStatsService = Depends(
        get_earnings_stats_controller,
    ),
) -> list[dict[str, Any]]:
    """Get earnings table for a custom date range.

    Args:
        start_date: Start date in ISO format (YYYY-MM-DD).
        end_date: End date in ISO format (YYYY-MM-DD).
        controller: Injected EarningsStatsService.

    Returns:
        List of earnings records.

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
