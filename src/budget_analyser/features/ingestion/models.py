"""Ingestion feature DTOs.

Data transfer objects for CSV ingestion and upload results.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IngestionResult:
    """Result of a transaction ingestion operation.

    Captures the outcome of ingesting one or more CSV files,
    including how many transactions were processed, inserted,
    and skipped as duplicates.

    Attributes:
        success: Whether the ingestion succeeded.
        message: Human-readable status message.
        transactions_processed: Total transactions in the CSV.
        transactions_inserted: New transactions stored.
        duplicates_skipped: Transactions already in the DB.

    Example:
        >>> from budget_analyser.features.ingestion.models import (
        ...     IngestionResult,
        ... )
        >>> result = IngestionResult(
        ...     success=True,
        ...     message="Processed 50 transactions",
        ...     transactions_processed=50,
        ...     transactions_inserted=45,
        ...     duplicates_skipped=5,
        ... )
        >>> result.success
        True
    """

    success: bool
    message: str
    transactions_processed: int = 0
    transactions_inserted: int = 0
    duplicates_skipped: int = 0


@dataclass(frozen=True)
class UploadResult:
    """Result of an upload operation.

    Captures the outcome of uploading a bank statement CSV,
    including the destination path and ingestion statistics.

    Attributes:
        success: Whether the upload succeeded.
        message: Human-readable status message.
        destination_path: Path where the file was copied.
        transactions_inserted: New transactions stored.
        duplicates_skipped: Transactions already in the DB.

    Example:
        >>> from budget_analyser.features.ingestion.models import (
        ...     UploadResult,
        ... )
        >>> result = UploadResult(
        ...     success=True,
        ...     message="Uploaded successfully",
        ...     destination_path="/data/statements/citi.csv",
        ...     transactions_inserted=30,
        ... )
        >>> result.destination_path
        '/data/statements/citi.csv'
    """

    success: bool
    message: str
    destination_path: str | None = None
    transactions_inserted: int = 0
    duplicates_skipped: int = 0
