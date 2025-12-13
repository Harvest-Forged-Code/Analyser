"""Statement repository adapter (infrastructure).

Purpose:
    Load account statement CSV files from the filesystem.

Goal:
    Provide raw statement DataFrames to the controller without leaking IO details.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd

from budget_analyser.domain.errors import DataSourceError
from budget_analyser.domain.protocols import StatementRepository
from budget_analyser.infrastructure.ini_config import IniAppConfig


@dataclass(frozen=True)
class CsvStatementRepository(StatementRepository):
    """CSV-backed statement repository."""

    statement_dir: Path
    config: IniAppConfig

    def get_statements(self) -> Mapping[str, pd.DataFrame]:
        """Load all configured statements from disk.

        Steps:
            1. Read accounts from INI config sections.
            2. Build filesystem paths for each account CSV.
            3. Load each CSV into a DataFrame.

        Returns:
            Mapping of account_name -> raw statement DataFrame.

        Raises:
            DataSourceError: When a required statement file cannot be found.
        """
        # Accumulate per-account DataFrames.
        statements: dict[str, pd.DataFrame] = {}

        # Iterate both credit cards and checking accounts.
        for section in ("credit_cards", "checking_accounts"):
            # Read all account option names under this section.
            for account in self.config.list_accounts(section=section):
                # Build the expected CSV path.
                filename = self.config.get_statement_filename(section=section, account=account)
                path = self.statement_dir / filename
                try:
                    # Load CSV; allow pandas to infer types.
                    statements[account] = pd.read_csv(path)
                except FileNotFoundError as exc:
                    # Translate IO exceptions into a domain-level error.
                    raise DataSourceError(f"Statement file not found: {path}") from exc

        # Return mapping of all loaded statements.
        return statements
