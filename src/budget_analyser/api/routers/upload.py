"""Upload router for Budget Analyser API.

Provides endpoints for CSV statement upload and validation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from budget_analyser.api.dependencies import (
    get_upload_controller,
    invalidate_reports,
)
from budget_analyser.api.serializers import (
    UploadResultSchema,
    UploadRequest,
)
from budget_analyser.features.ingestion.controller import UploadController

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.get("/banks/{account_type}")
def get_available_banks(
    *,
    account_type: str,
    controller: UploadController = Depends(get_upload_controller),
) -> list[str]:
    """List available banks for a given account type.

    Args:
        account_type: Account type (e.g., "checking", "credit").
        controller: Injected UploadController.

    Returns:
        List of bank names.

    Raises:
        HTTPException: If account type is invalid.
    """
    try:
        return controller.get_available_banks(account_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/missing")
def get_missing_statements(
    *, controller: UploadController = Depends(get_upload_controller),
) -> list[dict[str, str]]:
    """Get list of missing statement periods.

    Args:
        controller: Injected UploadController.

    Returns:
        List of missing statement info dicts.
    """
    missing = controller.get_missing_statements()
    return [
        {
            "account_type": m.account_type,
            "bank_name": m.bank_name,
            "period": str(m.period),
            "expected_file": m.expected_file,
        }
        for m in missing
    ]


@router.get("/status")
def get_bank_upload_status(
    *, controller: UploadController = Depends(get_upload_controller),
) -> dict[str, dict[str, list[str]]]:
    """Get upload status by account type and bank.

    Args:
        controller: Injected UploadController.

    Returns:
        Nested dict with uploaded periods by account type and bank.
    """
    status = controller.get_bank_upload_status()
    # Convert pd.Period objects to strings
    return {
        account_type: {
            bank: [str(p) for p in periods]
            for bank, periods in banks.items()
        }
        for account_type, banks in status.items()
    }


@router.post("/validate")
def validate_csv(
    *,
    file_path: str,
    bank_name: str,
    controller: UploadController = Depends(get_upload_controller),
) -> dict[str, bool | str | int]:
    """Validate a CSV file before upload.

    Args:
        file_path: Path to the CSV file.
        bank_name: Bank name for formatter selection.
        controller: Injected UploadController.

    Returns:
        Dict with validation result and metadata.

    Raises:
        HTTPException: If validation fails.
    """
    try:
        result = controller.validate_csv(file_path, bank_name)
        return {
            "valid": result.valid,
            "message": result.message,
            "row_count": result.row_count,
            "date_range": result.date_range,
        }
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=400, detail=f"Validation error: {e}",
        ) from e


@router.post("", response_model=UploadResultSchema)
def upload_statement(
    *,
    body: UploadRequest,
    controller: UploadController = Depends(get_upload_controller),
) -> UploadResultSchema:
    """Upload and process a bank statement CSV file.

    Args:
        body: UploadRequest with file_path, bank_name, account_type.
        controller: Injected UploadController.

    Returns:
        UploadResultSchema with processing results.

    Raises:
        HTTPException: If upload fails.
    """
    try:
        result = controller.upload_statement(
            file_path=body.file_path,
            bank_name=body.bank_name,
            account_type=body.account_type,
        )

        # Invalidate reports after successful upload
        if result.success:
            invalidate_reports()

        return UploadResultSchema(
            success=result.success,
            message=result.message,
            destination_path=result.destination_path,
            transactions_inserted=result.transactions_inserted,
            duplicates_skipped=result.duplicates_skipped,
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=400, detail=f"Upload failed: {e}",
        ) from e
