"""Reports router for Budget Analyser API.

Provides endpoints for report generation and metadata.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from budget_analyser.api.dependencies import get_reports, invalidate_reports
from budget_analyser.api.serializers import (
    AvailableMonthsResponse,
    AvailableYearsResponse,
)
from budget_analyser.core.models import MonthlyReports

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate")
def generate_reports() -> dict[str, str]:
    """Regenerate all monthly reports from the database.

    Returns:
        Success message confirming regeneration.
    """
    invalidate_reports()
    return {"message": "Reports regenerated successfully"}


@router.get("/available-months", response_model=AvailableMonthsResponse)
def get_available_months(
    *, reports: list[MonthlyReports] = Depends(get_reports),
) -> AvailableMonthsResponse:
    """List all available report months.

    Args:
        reports: Injected reports cache.

    Returns:
        AvailableMonthsResponse with list of month strings.
    """
    months = [str(r.month) for r in reports]
    return AvailableMonthsResponse(months=months)


@router.get("/available-years", response_model=AvailableYearsResponse)
def get_available_years(
    *, reports: list[MonthlyReports] = Depends(get_reports),
) -> AvailableYearsResponse:
    """List all unique years with reports.

    Args:
        reports: Injected reports cache.

    Returns:
        AvailableYearsResponse with list of year integers.
    """
    years = sorted({r.month.year for r in reports})
    return AvailableYearsResponse(years=years)
