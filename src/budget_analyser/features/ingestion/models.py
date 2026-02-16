"""Ingestion feature DTOs.

Data transfer objects for CSV ingestion and upload results.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IngestionResult:
    """Result of a transaction ingestion operation.

    Attributes:
        success: Whether the ingestion succeeded.
        message: Human-readable status message.
        transactions_processed: Total transactions in the CSV.
        transactions_inserted: New transactions stored.
        duplicates_skipped: Transactions already in the DB.
    """

    success: bool
    message: str
    transactions_processed: int = 0
    transactions_inserted: int = 0
    duplicates_skipped: int = 0


@dataclass(frozen=True)
class UploadResult:
    """Result of an upload operation.

    Attributes:
        success: Whether the upload succeeded.
        message: Human-readable status message.
        destination_path: Path where the file was copied.
        transactions_inserted: New transactions stored.
        duplicates_skipped: Transactions already in the DB.
    """

    success: bool
    message: str
    destination_path: str | None = None
    transactions_inserted: int = 0
    duplicates_skipped: int = 0
