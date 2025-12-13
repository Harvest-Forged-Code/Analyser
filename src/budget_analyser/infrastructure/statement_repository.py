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
    statement_dir: Path
    config: IniAppConfig

    def get_statements(self) -> Mapping[str, pd.DataFrame]:
        statements: dict[str, pd.DataFrame] = {}

        for section in ("credit_cards", "checking_accounts"):
            for account in self.config.list_accounts(section=section):
                filename = self.config.get_statement_filename(section=section, account=account)
                path = self.statement_dir / filename
                try:
                    statements[account] = pd.read_csv(path)
                except FileNotFoundError as exc:
                    raise DataSourceError(f"Statement file not found: {path}") from exc

        return statements
