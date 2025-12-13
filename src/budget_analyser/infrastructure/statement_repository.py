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

import logging
import pandas as pd

from budget_analyser.domain.errors import DataSourceError
from budget_analyser.domain.protocols import StatementRepository
from budget_analyser.infrastructure.ini_config import IniAppConfig


@dataclass(frozen=True)
class CsvStatementRepository(StatementRepository):
    """CSV-backed statement repository."""

    statement_dir: Path
    config: IniAppConfig
    logger: logging.Logger | None = None

    def _log(self, level: int, msg: str, *args) -> None:
        log = self.logger or logging.getLogger("budget_analyser.gui")
        try:
            log.log(level, msg, *args)
        except Exception:
            pass

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
                    # Log before read for traceability
                    self._log(
                        logging.INFO,
                        "Loading statement: section=%s account=%s file=%s",
                        section,
                        account,
                        str(path.resolve()),
                    )
                    # Load CSV; allow pandas to infer types.
                    df = pd.read_csv(path)
                    statements[account] = df
                    self._log(
                        logging.INFO,
                        "Loaded statement: account=%s rows=%s cols=%s",
                        account,
                        len(df.index),
                        len(df.columns),
                    )
                except FileNotFoundError as exc:
                    # Translate IO exceptions into a domain-level error with context.
                    self._log(
                        logging.ERROR,
                        "Statement file not found for account=%s path=%s",
                        account,
                        str(path.resolve()),
                    )
                    raise DataSourceError(f"Statement file not found: {path}") from exc
                except Exception as exc:  # pragma: no cover - defensive
                    self._log(
                        logging.ERROR,
                        "Failed reading CSV for account=%s path=%s error=%s",
                        account,
                        str(path.resolve()),
                        exc,
                    )
                    raise DataSourceError(f"Failed reading CSV for {account}: {path}") from exc

        # Return mapping of all loaded statements.
        return statements
