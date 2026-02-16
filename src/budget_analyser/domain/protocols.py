"""Domain protocols (interfaces).

Backward-compatibility shim: re-exports from core.protocols.
New code should import from budget_analyser.core.protocols directly.
"""

from budget_analyser.core.protocols import (  # pylint: disable=unused-import  # noqa: F401
    StatementRepository,
    ColumnMappingProvider,
    CategoryMappingProvider,
)
