"""Column mapping provider (infrastructure).

Purpose:
    Expose per-account CSV column mapping so formatters can normalize statements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from budget_analyser.domain.protocols import ColumnMappingProvider
from budget_analyser.infrastructure.ini_config import IniAppConfig


@dataclass(frozen=True)
class IniColumnMappingProvider(ColumnMappingProvider):
    """INI-backed column mapping provider."""

    config: IniAppConfig

    def get_column_mapping(self, account_name: str) -> Mapping[str, str]:
        """Get a source->desired column mapping for the specified account."""
        # Delegate to the INI adapter.
        return self.config.get_column_mapping(account_name=account_name)
