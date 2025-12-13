"""Category mappers dataclass (domain typing).

Single responsibility:
    Hold keyword mapping dictionaries used by the transaction processor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class CategoryMappers:
    """Keyword mappers used by the TransactionProcessor.

    Attributes:
        description_to_sub_category: Mapping of sub_category -> keywords list.
        sub_category_to_category: Mapping of category -> keywords list.
    """

    description_to_sub_category: Mapping[str, list[str]]
    sub_category_to_category: Mapping[str, list[str]]


__all__ = ["CategoryMappers"]
