"""Payments reconciliation router for Budget Analyser API.

Provides endpoints for payment pair matching and
reconciliation status.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from budget_analyser.api.dependencies import (
    get_payment_reconciliation_service,
)
from budget_analyser.features.payments.service import (
    PaymentReconciliationService,
)

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _pair_to_dict(pair: object) -> dict[str, Any]:
    """Convert a PaymentPair to a JSON-safe dict.

    Args:
        pair: PaymentPair instance.

    Returns:
        Dict with serialized payment pair data.
    """
    result: dict[str, Any] = {
        "status": pair.status,
        "amount": pair.amount,
        "source_account": pair.source_account,
        "destination_account": pair.destination_account,
        "payment_date": pair.payment_date,
        "confirmation_date": pair.confirmation_date,
    }

    if pair.payment_made:
        result["payment_made"] = _serialize_record(
            pair.payment_made,
        )
    if pair.payment_confirmation:
        result["payment_confirmation"] = _serialize_record(
            pair.payment_confirmation,
        )

    return result


def _serialize_record(
    record: dict[str, object],
) -> dict[str, Any]:
    """Serialize a transaction record dict for JSON.

    Args:
        record: Raw transaction record dict.

    Returns:
        Dict with date values converted to strings.
    """
    result: dict[str, Any] = {}
    for key, val in record.items():
        if hasattr(val, "strftime"):
            result[key] = val.strftime("%Y-%m-%d")
        else:
            result[key] = val
    return result


@router.get("/periods")
def get_available_periods(
    *,
    service: PaymentReconciliationService = Depends(
        get_payment_reconciliation_service,
    ),
) -> list[str]:
    """List all periods with payment transactions.

    Args:
        service: Injected PaymentReconciliationService.

    Returns:
        Sorted list of year-month strings.
    """
    return service.get_available_periods()


@router.get("/reconciliation/{period}")
def get_reconciliation(
    *,
    period: str,
    service: PaymentReconciliationService = Depends(
        get_payment_reconciliation_service,
    ),
) -> dict[str, Any]:
    """Get reconciliation summary for a specific period.

    Args:
        period: Year-month string (e.g. "2026-01").
        service: Injected PaymentReconciliationService.

    Returns:
        Reconciliation summary with matched and pending pairs.
    """
    summary = service.reconcile(period=period)
    return {
        "period": summary.period,
        "matched_pairs": [
            _pair_to_dict(p) for p in summary.matched_pairs
        ],
        "pending_payments": [
            _pair_to_dict(p) for p in summary.pending_payments
        ],
        "total_matched": summary.total_matched,
        "total_pending": summary.total_pending,
        "match_rate": summary.match_rate,
    }


@router.get("/reconciliation")
def get_reconciliation_all(
    *,
    service: PaymentReconciliationService = Depends(
        get_payment_reconciliation_service,
    ),
) -> dict[str, Any]:
    """Get reconciliation summary for all periods.

    Args:
        service: Injected PaymentReconciliationService.

    Returns:
        Reconciliation summary across all available data.
    """
    summary = service.reconcile(period="ALL")
    return {
        "period": summary.period,
        "matched_pairs": [
            _pair_to_dict(p) for p in summary.matched_pairs
        ],
        "pending_payments": [
            _pair_to_dict(p) for p in summary.pending_payments
        ],
        "total_matched": summary.total_matched,
        "total_pending": summary.total_pending,
        "match_rate": summary.match_rate,
    }
