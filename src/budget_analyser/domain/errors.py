"""Domain exceptions.

Purpose:
    Define domain-specific exceptions that represent business/data constraints.

Goal:
    Allow the presentation layer to translate domain failures into user-facing messages
    without leaking infrastructure implementation details.
"""


class DomainError(Exception):
    """Base class for all domain-level errors."""


class ValidationError(DomainError):
    """Raised when user input or provided data is invalid."""


class MappingNotFoundError(DomainError):
    """Raised when a required mapping is missing."""


class DataSourceError(DomainError):
    """Raised when a required external data source cannot be loaded."""
