class DomainError(Exception):
    """Base class for domain-level errors."""


class ValidationError(DomainError):
    """Raised when user input or provided data is invalid."""


class MappingNotFoundError(DomainError):
    """Raised when a required mapping is missing."""


class DataSourceError(DomainError):
    """Raised when a required external data source cannot be loaded."""
