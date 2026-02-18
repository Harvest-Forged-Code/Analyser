"""Payments router for Budget Analyser API.

Provides endpoints for payment reconciliation.
"""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from budget_analyser.api.dependencies import get_payments_controller
from budget_analyser.api.serializers import PaymentsReconciliationSummarySchema
from budget_analyser.features.payments.service import (
    PaymentsReconciliationService,
)

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts with date serialization.

    Args:
        df: DataFrame to convert, may be None or empty.

    Returns:
        List of row dictionaries with dates formatted as YYYY-MM-DD.
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
    *, service: PaymentsReconciliationService = Depends(
        get_payments_controller,
    ),
) -> list[str]:
    """List all available months with payment data.

    Args:
        service: Injected PaymentsReconciliationService.

    Returns:
        List of month strings (e.g., "2024-01").
    """
    return [str(p) for p in service.available_months()]


@router.get("/{period}", response_model=PaymentsReconciliationSummarySchema)
def get_payment_data(
    *,
    period: str,
    service: PaymentsReconciliationService = Depends(
        get_payments_controller,
    ),
) -> PaymentsReconciliationSummarySchema:
    """Get payment reconciliation data for a specific period.

    Args:
        period: Month period string (e.g., "2024-01").
        service: Injected PaymentsReconciliationService.

    Returns:
        PaymentsReconciliationSummarySchema with payments and confirmations.

    Raises:
        HTTPException: If period is invalid or data not found.
    """
    try:
        period_obj = pd.Period(period)
        data = service.data(period_obj)

        return PaymentsReconciliationSummarySchema(
            period=str(data.period),
            payments_made=_df_to_records(data.payments_made),
            payment_confirmations=_df_to_records(data.payment_confirmations),
            total_payments_made=data.total_payments_made,
            total_payment_confirmations=data.total_payment_confirmations,
            difference=data.difference,
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=404, detail=f"Invalid period or data not found: {e}",
        ) from e
