"""Mappers feature module.

Provides category/sub-category mapping management and
categorization suggestions for unmapped transactions.
"""

from budget_analyser.features.mappers.models import (
    Suggestion,
    SuggestionResult,
    JsonCategoryMappingProvider,
    JsonCashflowMappingProvider,
    JsonCategoryMappingStore,
    JsonCashflowMappingStore,
)
from budget_analyser.features.mappers.suggestion_service import (
    CategorizationSuggestionEngine,
    create_suggestion_engine,
    MERCHANT_PATTERNS,
)
from budget_analyser.features.mappers.service import (
    MapperService,
    MapperController,
)
from budget_analyser.features.mappers.cashflow_service import (
    CashflowMapperService,
    CashflowMapperController,
)
from budget_analyser.features.mappers.sub_category_service import (
    SubCategoryMapperService,
    SubCategoryMapperController,
)
from budget_analyser.features.mappers.validation import (
    MappingValidationService,
    ValidationIssue,
    ValidationReport,
    validate_mappings,
)

__all__ = [
    "Suggestion",
    "SuggestionResult",
    "CategorizationSuggestionEngine",
    "create_suggestion_engine",
    "MERCHANT_PATTERNS",
    "MapperService",
    "MapperController",
    "CashflowMapperService",
    "CashflowMapperController",
    "SubCategoryMapperService",
    "SubCategoryMapperController",
    "JsonCategoryMappingProvider",
    "JsonCashflowMappingProvider",
    "JsonCategoryMappingStore",
    "JsonCashflowMappingStore",
    "MappingValidationService",
    "ValidationIssue",
    "ValidationReport",
    "validate_mappings",
]
