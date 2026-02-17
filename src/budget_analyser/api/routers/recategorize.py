"""Recategorize router for Budget Analyser API.

Provides an endpoint to re-apply keyword mappers to all
stored transactions, updating categories retroactively.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from budget_analyser.api.dependencies import (
    get_recategorize_controller,
    invalidate_reports,
)
from budget_analyser.features.recategorize.controller import (
    RecategorizeController,
)

router = APIRouter(prefix="/api/recategorize", tags=["recategorize"])


@router.post("")
def recategorize_transactions(
    *,
    controller: RecategorizeController = Depends(
        get_recategorize_controller,
    ),
) -> dict[str, bool | str | int]:
    """Re-apply keyword mappers to all stored transactions.

    Args:
        controller: Injected RecategorizeController.

    Returns:
        Dict with success status, message, and update counts.

    Raises:
        HTTPException: If recategorization fails.
    """
    try:
        result = controller.run()

        if result.success:
            invalidate_reports()

        return {
            "success": result.success,
            "message": result.message,
            "total_transactions": result.total_transactions,
            "updated_count": result.updated_count,
        }
    except Exception as exc:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=500,
            detail=f"Recategorization failed: {exc}",
        ) from exc
