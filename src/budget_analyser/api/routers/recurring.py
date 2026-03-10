"""Recurring payments router for Budget Analyser API."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

from budget_analyser.api.dependencies import (
    get_recurring_analytics_service,
)
from budget_analyser.api.serializers import (
    AddRecurringRequest,
    MarkExpectedRequest,
    RecurringAnomalySchema,
    RecurringDetectionSchema,
    RecurringSummarySchema,
    RecurringTransactionSchema,
    UpdateRecurringRequest,
)
from budget_analyser.features.recurring.service import (
    RecurringAnalyticsService,
)

router = APIRouter(prefix="/api/recurring", tags=["recurring"])


# ------------------------------------------------------------------
# Fixed-path routes (MUST come before parameterized routes)
# ------------------------------------------------------------------

@router.get("/detect", response_model=list[RecurringDetectionSchema])
def detect_recurring(
    *,
    service: RecurringAnalyticsService = Depends(
        get_recurring_analytics_service,
    ),
) -> list[RecurringDetectionSchema]:
    """Auto-detect recurring transactions from transaction history.

    Returns:
        List of detected recurring patterns.
    """
    detections = service.detect_recurring_transactions()
    return [
        RecurringDetectionSchema(**asdict(d)) for d in detections
    ]


@router.get("/summary", response_model=RecurringSummarySchema)
def get_summary(
    *,
    service: RecurringAnalyticsService = Depends(
        get_recurring_analytics_service,
    ),
) -> RecurringSummarySchema:
    """Get analytics summary for recurring transactions.

    Returns:
        RecurringSummarySchema with aggregated metrics.
    """
    summary = service.get_summary()
    return RecurringSummarySchema(**asdict(summary))


@router.get("/anomalies", response_model=list[RecurringAnomalySchema])
def get_anomalies(
    *,
    service: RecurringAnalyticsService = Depends(
        get_recurring_analytics_service,
    ),
) -> list[RecurringAnomalySchema]:
    """Get all unresolved anomalies.

    Returns:
        List of unresolved recurring anomalies.
    """
    anomalies = service.get_anomalies()
    return [
        RecurringAnomalySchema(**asdict(a)) for a in anomalies
    ]


@router.patch(
    "/anomalies/{anomaly_id}/resolve",
    response_model=dict[str, bool],
)
def resolve_anomaly(
    anomaly_id: int,
    *,
    service: RecurringAnalyticsService = Depends(
        get_recurring_analytics_service,
    ),
) -> dict[str, bool]:
    """Resolve a recurring anomaly.

    Args:
        anomaly_id: The primary key of the anomaly record.

    Returns:
        Confirmation dict with resolved status.

    Raises:
        HTTPException: 404 if anomaly not found.
    """
    resolved = service.resolve_anomaly(anomaly_id)
    if not resolved:
        raise HTTPException(
            status_code=404, detail="Anomaly not found",
        )
    return {"resolved": True}


# ------------------------------------------------------------------
# Collection routes
# ------------------------------------------------------------------

@router.get("", response_model=list[RecurringTransactionSchema])
def list_recurring(
    active_only: bool = False,
    *,
    service: RecurringAnalyticsService = Depends(
        get_recurring_analytics_service,
    ),
) -> list[RecurringTransactionSchema]:
    """List all recurring transactions.

    Args:
        active_only: If True, return only active entries.

    Returns:
        List of recurring transactions.
    """
    items = service.get_all_recurring(active_only=active_only)
    return [
        RecurringTransactionSchema(**asdict(item)) for item in items
    ]


@router.post("", response_model=RecurringTransactionSchema)
def add_recurring(
    body: AddRecurringRequest,
    *,
    service: RecurringAnalyticsService = Depends(
        get_recurring_analytics_service,
    ),
) -> RecurringTransactionSchema:
    """Add a new recurring transaction manually.

    Args:
        body: Request body with recurring transaction details.

    Returns:
        The created recurring transaction.
    """
    result = service.add_manual_recurring(
        description=body.description,
        expected_amount=body.expected_amount,
        frequency=body.frequency,
        category=body.category,
        sub_category=body.sub_category,
    )
    return RecurringTransactionSchema(**asdict(result))


# ------------------------------------------------------------------
# Item routes (parameterized by recurring_id)
# ------------------------------------------------------------------

@router.put(
    "/{recurring_id}",
    response_model=RecurringTransactionSchema,
)
def update_recurring(
    recurring_id: int,
    body: UpdateRecurringRequest,
    *,
    service: RecurringAnalyticsService = Depends(
        get_recurring_analytics_service,
    ),
) -> RecurringTransactionSchema:
    """Update a recurring transaction.

    Args:
        recurring_id: The primary key of the recurring record.
        body: Request body with fields to update.

    Returns:
        The updated recurring transaction.

    Raises:
        HTTPException: 404 if recurring transaction not found.
    """
    updates = {
        k: v for k, v in body.model_dump().items() if v is not None
    }
    result = service.update_recurring(recurring_id, **updates)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Recurring transaction not found",
        )
    return RecurringTransactionSchema(**asdict(result))


@router.delete("/{recurring_id}", response_model=dict[str, bool])
def delete_recurring(
    recurring_id: int,
    *,
    service: RecurringAnalyticsService = Depends(
        get_recurring_analytics_service,
    ),
) -> dict[str, bool]:
    """Delete a recurring transaction.

    Args:
        recurring_id: The primary key of the recurring record.

    Returns:
        Confirmation dict with deleted status.

    Raises:
        HTTPException: 404 if recurring transaction not found.
    """
    deleted = service.delete_recurring(recurring_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Recurring transaction not found",
        )
    return {"deleted": True}


@router.patch(
    "/{recurring_id}/confirm",
    response_model=RecurringTransactionSchema,
)
def confirm_recurring(
    recurring_id: int,
    *,
    service: RecurringAnalyticsService = Depends(
        get_recurring_analytics_service,
    ),
) -> RecurringTransactionSchema:
    """Confirm a detected recurring transaction.

    Args:
        recurring_id: The primary key of the recurring record.

    Returns:
        The confirmed recurring transaction.

    Raises:
        HTTPException: 404 if recurring transaction not found.
    """
    result = service.confirm_detection(recurring_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Recurring transaction not found",
        )
    return RecurringTransactionSchema(**asdict(result))


@router.patch(
    "/{recurring_id}/dismiss",
    response_model=RecurringTransactionSchema,
)
def dismiss_recurring(
    recurring_id: int,
    *,
    service: RecurringAnalyticsService = Depends(
        get_recurring_analytics_service,
    ),
) -> RecurringTransactionSchema:
    """Dismiss a detected recurring transaction.

    Args:
        recurring_id: The primary key of the recurring record.

    Returns:
        The dismissed recurring transaction.

    Raises:
        HTTPException: 404 if recurring transaction not found.
    """
    result = service.dismiss_detection(recurring_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Recurring transaction not found",
        )
    return RecurringTransactionSchema(**asdict(result))


@router.patch(
    "/{recurring_id}/expected",
    response_model=RecurringTransactionSchema,
)
def mark_expected(
    recurring_id: int,
    body: MarkExpectedRequest,
    *,
    service: RecurringAnalyticsService = Depends(
        get_recurring_analytics_service,
    ),
) -> RecurringTransactionSchema:
    """Mark a recurring transaction as expected or unexpected.

    Args:
        recurring_id: The primary key of the recurring record.
        body: Request body with is_expected flag.

    Returns:
        The updated recurring transaction.

    Raises:
        HTTPException: 404 if recurring transaction not found.
    """
    result = service.mark_expected(
        recurring_id, is_expected=body.is_expected,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Recurring transaction not found",
        )
    return RecurringTransactionSchema(**asdict(result))
