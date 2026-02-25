"""Ingestion feature -- CSV upload and transaction processing.

Public API:
    IngestionResult               -- Result of an ingestion operation.
    UploadResult                  -- Result of an upload operation.
    ValidationResult              -- Result of a CSV validation check.
    UploadStats                   -- Aggregate upload statistics.
    UploadHistoryEntry            -- Single upload history log entry.
    UploadHistoryModel            -- SQLite-backed upload history storage.
    IniColumnMappingProvider      -- INI-backed column mapping provider.
    CsvStatementRepository        -- CSV-backed statement repository.
    TransactionIngestionService   -- Service to ingest CSVs into the DB.
    UploadService                 -- Service for bank statement uploads.
"""

from __future__ import annotations

from budget_analyser.features.ingestion.models import (
    IngestionResult,
    UploadResult,
    ValidationResult,
    UploadStats,
    UploadHistoryEntry,
    UploadHistoryModel,
    IniColumnMappingProvider,
    CsvStatementRepository,
)
from budget_analyser.features.ingestion.service import (
    TransactionIngestionService,
    UploadService,
)

__all__ = [
    "IngestionResult",
    "UploadResult",
    "ValidationResult",
    "UploadStats",
    "UploadHistoryEntry",
    "UploadHistoryModel",
    "IniColumnMappingProvider",
    "CsvStatementRepository",
    "TransactionIngestionService",
    "UploadService",
]
