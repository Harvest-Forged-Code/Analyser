"""Transaction ingestion service (domain logic).

Backward-compatibility shim: re-exports from features.ingestion.
New code should import from budget_analyser.features.ingestion directly.
"""

from budget_analyser.features.ingestion import (  # pylint: disable=unused-import  # noqa: F401
    IngestionResult,
    TransactionIngestionService,
)
