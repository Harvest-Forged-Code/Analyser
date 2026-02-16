"""Domain exceptions.

Backward-compatibility shim: re-exports from core.errors.
New code should import from budget_analyser.core.errors directly.
"""

from budget_analyser.core.errors import (  # pylint: disable=unused-import  # noqa: F401
    DomainError,
    ValidationError,
    MappingNotFoundError,
    DataSourceError,
)
