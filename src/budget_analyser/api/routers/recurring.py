"""Recurring transactions router for Budget Analyser API.

Provides endpoints for recurring transaction management and analysis.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, Query

from budget_analyser.api.dependencies import (
    get_recurring_controller,
    get_reports,
)
from budget_analyser.api.serializers import (
    RecurringTransactionSchema,
    AddRecurringRequest,
)
from budget_analyser.core.models import MonthlyReports
from budget_analyser.features.recurring.controller import RecurringController

router = APIRouter(prefix="/api/recurring", tags=["recurring"])


def _all_transactions_df(reports: list[MonthlyReports]) -> pd.DataFrame:
    """Concatenate all transactions from reports."""
    frames = []
    for r in reports:
        if r.transactions is not None and not r.transactions.empty:
            frames.append(r.transactions)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert DataFrame to list of dicts with date serialization."""
    if df is None or df.empty:
        return []
    result = df.copy()
    for col in result.columns:
        if pd.api.types.is_datetime64_any_dtype(result[col]):
            result[col] = result[col].dt.strftime("%Y-%m-%d")
    return result.to_dict(orient="records")


@router.get("", response_model=list[RecurringTransactionSchema])
def get_all_recurring_transactions(
    *,
    active_only: bool = Query(False),
    controller: RecurringController = Depends(get_recurring_controller),
) -> list[RecurringTransactionSchema]:
    """List all recurring transactions.

    Args:
        active_only: If True, return only active recurring transactions.
        controller: Injected RecurringController.

    Returns:
        List of RecurringTransactionSchema.
    """
    transactions = controller.get_all_recurring_transactions(
        active_only=active_only,
    )
    return [
        RecurringTransactionSchema(
            id=t.id,
            description=t.description,
            expected_amount=t.expected_amount,
            frequency=t.frequency.value,
            category=t.category,
            sub_category=t.sub_category,
            last_occurrence=t.last_occurrence.strftime("%Y-%m-%d"),
            is_active=t.is_active,
        )
        for t in transactions
    ]


@router.post("")
def add_recurring_transaction(
    *,
    body: AddRecurringRequest,
    controller: RecurringController = Depends(get_recurring_controller),
) -> dict[str, str]:
    """Add a new recurring transaction.

    Args:
        body: AddRecurringRequest with transaction details.
        controller: Injected RecurringController.

    Returns:
        Success message.
    """
    controller.add_recurring_transaction(
        description=body.description,
        expected_amount=body.expected_amount,
        frequency=body.frequency,
        category=body.category,
        sub_category=body.sub_category,
    )
    return {"message": "Recurring transaction added successfully"}


@router.delete("/{recurring_id}")
def delete_recurring_transaction(
    *,
    recurring_id: int,
    controller: RecurringController = Depends(get_recurring_controller),
) -> dict[str, str]:
    """Delete a recurring transaction.

    Args:
        recurring_id: Recurring transaction ID.
        controller: Injected RecurringController.

    Returns:
        Success message.
    """
    controller.delete_recurring_transaction(recurring_id=recurring_id)
    return {"message": "Recurring transaction deleted successfully"}


@router.patch("/{recurring_id}/deactivate")
def deactivate_recurring_transaction(
    *,
    recurring_id: int,
    controller: RecurringController = Depends(get_recurring_controller),
) -> dict[str, str]:
    """Deactivate a recurring transaction.

    Args:
        recurring_id: Recurring transaction ID.
        controller: Injected RecurringController.

    Returns:
        Success message.
    """
    controller.deactivate_recurring_transaction(recurring_id=recurring_id)
    return {"message": "Recurring transaction deactivated successfully"}


@router.get("/summary")
def get_recurring_summary(
    *,
    reports: list[MonthlyReports] = Depends(get_reports),
    controller: RecurringController = Depends(get_recurring_controller),
) -> dict[str, Any]:
    """Get summary of recurring transactions status.

    Args:
        reports: Injected reports cache.
        controller: Injected RecurringController.

    Returns:
        Dict with recurring summary metrics.
    """
    transactions_df = _all_transactions_df(reports)
    summary = controller.get_recurring_summary(transactions_df)

    return {
        "total_recurring": summary.total_recurring,
        "active_recurring": summary.active_recurring,
        "total_expected_monthly": summary.total_expected_monthly,
        "total_actual_monthly": summary.total_actual_monthly,
        "variance": summary.variance,
        "by_frequency": summary.by_frequency,
    }


@router.get("/detect")
def detect_recurring_transactions(
    *,
    reports: list[MonthlyReports] = Depends(get_reports),
    controller: RecurringController = Depends(get_recurring_controller),
) -> list[dict[str, Any]]:
    """Detect potential recurring transactions from historical data.

    Args:
        reports: Injected reports cache.
        controller: Injected RecurringController.

    Returns:
        List of detected recurring transaction records.
    """
    transactions_df = _all_transactions_df(reports)
    detected = controller.detect_recurring_transactions(transactions_df)
    return _df_to_records(detected)


@router.get("/anomalies")
def check_recurring_anomalies(
    *,
    reports: list[MonthlyReports] = Depends(get_reports),
    controller: RecurringController = Depends(get_recurring_controller),
) -> list[dict[str, Any]]:
    """Check for anomalies in recurring transactions.

    Args:
        reports: Injected reports cache.
        controller: Injected RecurringController.

    Returns:
        List of anomaly records.
    """
    transactions_df = _all_transactions_df(reports)
    anomalies = controller.check_recurring_anomalies(transactions_df)

    return [
        {
            "recurring_id": a.recurring_id,
            "description": a.description,
            "expected_amount": a.expected_amount,
            "actual_amount": a.actual_amount,
            "difference": a.difference,
            "expected_date": a.expected_date.strftime("%Y-%m-%d"),
            "actual_date": (
                a.actual_date.strftime("%Y-%m-%d") if a.actual_date else None
            ),
            "anomaly_type": a.anomaly_type.value,
            "severity": a.severity.value,
        }
        for a in anomalies
    ]
