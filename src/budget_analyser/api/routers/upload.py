"""Upload router for Budget Analyser API."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from budget_analyser.api.dependencies import (
    get_upload_controller,
    invalidate_reports,
)
from budget_analyser.api.serializers import (
    UploadResultSchema,
    UploadRequest,
    ValidationResultSchema,
    UploadStatsSchema,
    UploadHistoryEntrySchema,
    ValidateRequest,
)
from budget_analyser.features.ingestion.service import (
    UploadService as UploadController,
)

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.get("/banks/{account_type}")
def get_available_banks(
    *,
    account_type: str,
    controller: UploadController = Depends(
        get_upload_controller,
    ),
) -> list[str]:
    """List available banks for a given account type."""
    try:
        return controller.get_available_banks(account_type)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=str(e),
        ) from e


@router.get("/missing")
def get_missing_statements(
    *,
    controller: UploadController = Depends(
        get_upload_controller,
    ),
) -> list[dict[str, str]]:
    """Get list of missing statement files."""
    missing = controller.get_missing_statements()
    return [
        {
            "bank_name": m[0],
            "account_type": m[1],
            "expected_file": m[2],
        }
        for m in missing
    ]


@router.get("/status")
def get_bank_upload_status(
    *,
    controller: UploadController = Depends(
        get_upload_controller,
    ),
) -> list[dict[str, object]]:
    """Get upload status for all configured banks."""
    status = controller.get_bank_upload_status()
    return [
        {
            "bank_name": s[0],
            "account_type": s[1],
            "is_uploaded": s[2],
        }
        for s in status
    ]


@router.post("/validate", response_model=ValidationResultSchema)
def validate_csv(
    *,
    body: ValidateRequest,
    controller: UploadController = Depends(
        get_upload_controller,
    ),
) -> ValidationResultSchema:
    """Validate a CSV file before upload."""
    try:
        is_valid, message, _missing_cols = (
            controller.validate_csv(
                Path(body.file_path), body.bank_name,
            )
        )
        return ValidationResultSchema(
            valid=is_valid,
            message=message,
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {e}",
        ) from e


@router.get("/stats", response_model=UploadStatsSchema)
def get_upload_stats(
    *,
    controller: UploadController = Depends(
        get_upload_controller,
    ),
) -> UploadStatsSchema:
    """Return aggregate upload statistics."""
    try:
        stats = controller.get_upload_stats()
        return UploadStatsSchema(
            total_transactions=stats.total_transactions,
            total_accounts=stats.total_accounts,
            last_upload_date=stats.last_upload_date,
            total_uploads=stats.total_uploads,
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {e}",
        ) from e


@router.get(
    "/history",
    response_model=list[UploadHistoryEntrySchema],
)
def get_upload_history(
    *,
    controller: UploadController = Depends(
        get_upload_controller,
    ),
) -> list[UploadHistoryEntrySchema]:
    """Return recent upload history."""
    try:
        entries = controller.get_recent_history(limit=10)
        return [
            UploadHistoryEntrySchema(
                file_name=e.file_name,
                bank_name=e.bank_name,
                account_type=e.account_type,
                uploaded_at=e.uploaded_at,
                transactions_inserted=e.transactions_inserted,
            )
            for e in entries
        ]
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get history: {e}",
        ) from e


@router.post("", response_model=UploadResultSchema)
def upload_statement(
    *,
    body: UploadRequest,
    controller: UploadController = Depends(
        get_upload_controller,
    ),
) -> UploadResultSchema:
    """Upload and process a bank statement CSV file."""
    try:
        result = controller.upload_statement(
            source_path=Path(body.file_path),
            bank_name=body.bank_name,
            account_type=body.account_type,
        )
        if result.success:
            invalidate_reports()
        return UploadResultSchema(
            success=result.success,
            message=result.message,
            destination_path=result.destination_path,
            transactions_inserted=result.transactions_inserted,
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=400,
            detail=f"Upload failed: {e}",
        ) from e


@router.post(
    "/validate-file",
    response_model=ValidationResultSchema,
)
async def validate_csv_file(
    *,
    file: UploadFile,
    bank_name: str = Form(),
    controller: UploadController = Depends(
        get_upload_controller,
    ),
) -> ValidationResultSchema:
    """Validate an uploaded CSV file before processing."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False,
        ) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        is_valid, message, _missing_cols = (
            controller.validate_csv(
                Path(tmp_path), bank_name,
            )
        )
        return ValidationResultSchema(
            valid=is_valid,
            message=message,
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {e}",
        ) from e
    finally:
        if tmp_path:
            os.unlink(tmp_path)


@router.post("/file", response_model=UploadResultSchema)
async def upload_statement_file(
    *,
    file: UploadFile,
    bank_name: str = Form(),
    account_type: str = Form(),
    controller: UploadController = Depends(
        get_upload_controller,
    ),
) -> UploadResultSchema:
    """Upload and process a bank statement CSV via file upload."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False,
        ) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        result = controller.upload_statement(
            source_path=Path(tmp_path),
            bank_name=bank_name,
            account_type=account_type,
        )
        if result.success:
            invalidate_reports()
        return UploadResultSchema(
            success=result.success,
            message=result.message,
            destination_path=result.destination_path,
            transactions_inserted=result.transactions_inserted,
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=400,
            detail=f"Upload failed: {e}",
        ) from e
    finally:
        if tmp_path:
            os.unlink(tmp_path)
