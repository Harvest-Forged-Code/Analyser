"""Trends router for Budget Analyser API.

Provides endpoints for trend analysis, patterns, and anomalies.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, Query, HTTPException

from budget_analyser.api.dependencies import get_reports
from budget_analyser.api.serializers import (
    TrendAnalysisResultSchema,
    MonthlyTrendSchema,
    ParetoAnalysisSchema,
    ParetoItemSchema,
    WeeklyPatternSchema,
    DayPatternSchema,
    AnomalyReportSchema,
    AnomalySchema,
    BurnRateMetricsSchema,
)
from budget_analyser.core.models import MonthlyReports
from budget_analyser.features.trends.trend_analysis import (
    analyze_spending_trends,
    analyze_income_trends,
)
from budget_analyser.features.trends.spending_patterns import (
    SpendingPatternService,
)
from budget_analyser.features.trends.burn_rate import calculate_burn_rate

router = APIRouter(prefix="/api/trends", tags=["trends"])


def _all_transactions_df(reports: list[MonthlyReports]) -> pd.DataFrame:
    """Concatenate all transactions from reports."""
    frames = []
    for r in reports:
        if r.transactions is not None and not r.transactions.empty:
            frames.append(r.transactions)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@router.get("/spending", response_model=TrendAnalysisResultSchema)
def get_spending_trends(
    *,
    category: str | None = Query(None),
    reports: list[MonthlyReports] = Depends(get_reports),
) -> TrendAnalysisResultSchema:
    """Analyze spending trends over time.

    Args:
        category: Optional category filter.
        reports: Injected reports cache.

    Returns:
        TrendAnalysisResultSchema with MoM/YoY analysis.
    """
    transactions_df = _all_transactions_df(reports)
    result = analyze_spending_trends(transactions_df, category=category)

    return TrendAnalysisResultSchema(
        monthly_trends=[
            MonthlyTrendSchema(
                period=str(mt.period),
                value=mt.value,
                mom_change=mt.mom_change,
                mom_change_pct=mt.mom_change_pct,
                yoy_change=mt.yoy_change,
                yoy_change_pct=mt.yoy_change_pct,
                moving_avg_3m=mt.moving_avg_3m,
                moving_avg_6m=mt.moving_avg_6m,
                moving_avg_12m=mt.moving_avg_12m,
                direction=mt.direction.value,
            )
            for mt in result.monthly_trends
        ],
        overall_direction=result.overall_direction.value,
        average_mom_change_pct=result.average_mom_change_pct,
        volatility=result.volatility,
        highest_month=(
            str(result.highest_month) if result.highest_month else None
        ),
        lowest_month=str(result.lowest_month) if result.lowest_month else None,
    )


@router.get("/income", response_model=TrendAnalysisResultSchema)
def get_income_trends(
    *, reports: list[MonthlyReports] = Depends(get_reports),
) -> TrendAnalysisResultSchema:
    """Analyze income trends over time.

    Args:
        reports: Injected reports cache.

    Returns:
        TrendAnalysisResultSchema with MoM/YoY analysis.
    """
    transactions_df = _all_transactions_df(reports)
    result = analyze_income_trends(transactions_df)

    return TrendAnalysisResultSchema(
        monthly_trends=[
            MonthlyTrendSchema(
                period=str(mt.period),
                value=mt.value,
                mom_change=mt.mom_change,
                mom_change_pct=mt.mom_change_pct,
                yoy_change=mt.yoy_change,
                yoy_change_pct=mt.yoy_change_pct,
                moving_avg_3m=mt.moving_avg_3m,
                moving_avg_6m=mt.moving_avg_6m,
                moving_avg_12m=mt.moving_avg_12m,
                direction=mt.direction.value,
            )
            for mt in result.monthly_trends
        ],
        overall_direction=result.overall_direction.value,
        average_mom_change_pct=result.average_mom_change_pct,
        volatility=result.volatility,
        highest_month=(
            str(result.highest_month) if result.highest_month else None
        ),
        lowest_month=str(result.lowest_month) if result.lowest_month else None,
    )


@router.get("/pareto", response_model=ParetoAnalysisSchema)
def get_pareto_analysis(
    *,
    group_by: str = Query("category"),
    reports: list[MonthlyReports] = Depends(get_reports),
) -> ParetoAnalysisSchema:
    """Perform Pareto analysis (80/20 rule) on spending.

    Args:
        group_by: Grouping field (default "category").
        reports: Injected reports cache.

    Returns:
        ParetoAnalysisSchema with top contributors.
    """
    transactions_df = _all_transactions_df(reports)
    service = SpendingPatternService()
    result = service.pareto_analysis(
        transactions=transactions_df, group_by=group_by,
    )

    return ParetoAnalysisSchema(
        items=[
            ParetoItemSchema(
                category=item.category,
                amount=item.amount,
                percentage=item.percentage,
                cumulative_percentage=item.cumulative_percentage,
                is_top_80=item.is_top_80,
            )
            for item in result.items
        ],
        total_amount=result.total_amount,
        top_80_count=result.top_80_count,
        concentration_ratio=result.concentration_ratio,
    )


@router.get("/weekly-pattern", response_model=WeeklyPatternSchema)
def get_weekly_pattern(
    *, reports: list[MonthlyReports] = Depends(get_reports),
) -> WeeklyPatternSchema:
    """Analyze spending patterns by day of week.

    Args:
        reports: Injected reports cache.

    Returns:
        WeeklyPatternSchema with day-by-day breakdown.
    """
    transactions_df = _all_transactions_df(reports)
    service = SpendingPatternService()
    result = service.weekly_pattern(transactions=transactions_df)

    return WeeklyPatternSchema(
        day_patterns=[
            DayPatternSchema(
                day=dp.day.name,
                total_amount=dp.total_amount,
                transaction_count=dp.transaction_count,
                average_transaction=dp.average_transaction,
                percentage_of_week=dp.percentage_of_week,
            )
            for dp in result.day_patterns
        ],
        highest_day=result.highest_day.name if result.highest_day else None,
        lowest_day=result.lowest_day.name if result.lowest_day else None,
        weekend_percentage=result.weekend_percentage,
    )


@router.get("/anomalies", response_model=AnomalyReportSchema)
def get_anomalies(
    *, reports: list[MonthlyReports] = Depends(get_reports),
) -> AnomalyReportSchema:
    """Detect anomalies in spending patterns.

    Args:
        reports: Injected reports cache.

    Returns:
        AnomalyReportSchema with unusual transactions.
    """
    transactions_df = _all_transactions_df(reports)
    service = SpendingPatternService()
    result = service.detect_anomalies(transactions=transactions_df)

    return AnomalyReportSchema(
        anomalies=[
            AnomalySchema(
                transaction_date=a.transaction_date.strftime("%Y-%m-%d"),
                description=a.description,
                amount=a.amount,
                category=a.category,
                z_score=a.z_score,
                anomaly_type=a.anomaly_type.value,
                reason=a.reason,
            )
            for a in result.anomalies
        ],
        total_transactions=result.total_transactions,
        anomaly_rate=result.anomaly_rate,
    )


@router.get("/burn-rate/{year}/{month}", response_model=BurnRateMetricsSchema)
def get_burn_rate(
    *,
    year: int,
    month: int,
    budget_amount: float = Query(...),
    as_of_date: str | None = Query(None),
    reports: list[MonthlyReports] = Depends(get_reports),
) -> BurnRateMetricsSchema:
    """Calculate budget burn rate for a specific month.

    Args:
        year: Year as integer.
        month: Month as integer (1-12).
        budget_amount: Monthly budget limit.
        as_of_date: Optional as-of date (ISO format).
        reports: Injected reports cache.

    Returns:
        BurnRateMetricsSchema with burn rate analysis.

    Raises:
        HTTPException: If month not found or calculation fails.
    """
    try:
        # Find the report for the requested month
        period = pd.Period(f"{year}-{month:02d}")
        report = next((r for r in reports if r.month == period), None)

        if not report or report.expenses.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No expense data for {year}-{month:02d}",
            )

        # Parse as_of_date if provided
        as_of_date_obj = None
        if as_of_date:
            as_of_date_obj = date.fromisoformat(as_of_date)

        metrics = calculate_burn_rate(
            transactions=report.expenses,
            budget_amount=budget_amount,
            as_of_date=as_of_date_obj,
        )

        return BurnRateMetricsSchema(
            period_start=metrics.period_start.strftime("%Y-%m-%d"),
            period_end=metrics.period_end.strftime("%Y-%m-%d"),
            budget_amount=metrics.budget_amount,
            spent_amount=metrics.spent_amount,
            days_elapsed=metrics.days_elapsed,
            days_remaining=metrics.days_remaining,
            daily_burn_rate=metrics.daily_burn_rate,
            projected_total=metrics.projected_total,
            budget_remaining=metrics.budget_remaining,
            safe_daily_spend=metrics.safe_daily_spend,
            days_until_exhausted=metrics.days_until_exhausted,
            burn_rate_status=metrics.burn_rate_status.value,
            projected_over_under=metrics.projected_over_under,
            is_over_budget=metrics.is_over_budget,
            on_track=metrics.on_track,
            burn_rate_percentage=metrics.burn_rate_percentage,
            time_percentage=metrics.time_percentage,
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid parameters: {e}",
        ) from e
