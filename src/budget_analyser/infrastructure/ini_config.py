"""INI configuration adapter (infrastructure).

Purpose:
    Read the repository-shipped `config/budget_analyser.ini` file.

Goal:
    Provide typed access to accounts, statement filenames, and column mappings.

Notes:
    This is an infrastructure adapter; higher layers depend on its public methods.
"""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class IniAppConfig:
    """INI-backed configuration reader."""

    path: Path

    def _parser(self) -> configparser.ConfigParser:
        """Create and load a configparser for the configured INI file."""
        # Disable interpolation to avoid treating values like "%(x)s" as templates.
        parser = configparser.ConfigParser(interpolation=None)
        # Load INI file content.
        parser.read(self.path, encoding="utf-8")
        return parser

    def list_accounts(self, *, section: str) -> list[str]:
        """List account option names under an INI section.

        Args:
            section: INI section name (e.g., "credit_cards").

        Returns:
            List of account identifiers.
        """
        parser = self._parser()
        return list(parser.options(section))

    def get_statement_filename(self, *, section: str, account: str) -> str:
        """Return the statement filename for a given account.

        Args:
            section: INI section (credit_cards/checking_accounts).
            account: Account identifier.

        Returns:
            CSV filename.
        """
        parser = self._parser()
        return parser.get(section, account)

    def get_column_mapping(self, *, account_name: str) -> Mapping[str, str]:
        """Return source->desired column mapping for an account.

        Args:
            account_name: Account identifier (e.g., "citi").

        Returns:
            A mapping from source column names (from CSV) to desired canonical names.
        """
        parser = self._parser()
        section = f"{account_name}_map"
        # INI stores desired->source; invert to source->desired for pandas.rename.
        mapping_desired_to_source = dict(parser.items(section))
        return {source: desired for desired, source in mapping_desired_to_source.items()}
