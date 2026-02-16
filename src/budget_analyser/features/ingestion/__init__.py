"""Ingestion feature — CSV upload and transaction processing.

Public API:
    IngestionResult          — Result of an ingestion operation.
    UploadResult             — Result of an upload operation.
    TransactionIngestionService — Service to ingest CSVs into the DB.
    UploadController         — Controller for bank statement uploads.
"""

from __future__ import annotations

from budget_analyser.features.ingestion.models import (
    IngestionResult,
    UploadResult,
)
from budget_analyser.features.ingestion.service import (
    TransactionIngestionService,
)
from budget_analyser.features.ingestion.controller import (
    UploadController,
)

__all__ = [
    "IngestionResult",
    "UploadResult",
    "TransactionIngestionService",
    "UploadController",
]
