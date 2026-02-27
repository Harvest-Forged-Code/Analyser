"""Application configuration: settings/env parsing.

Purpose:
    Provide a single `Settings` object that contains all runtime configuration.

Goal:
    Avoid hard-coded paths/secrets and keep configuration centralized.

Steps:
    1. Locate the project root.
    2. Load optional `.env` into `os.environ` (without overwriting existing env).
    3. Read required setting values from environment with safe defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _project_root() -> Path:
    """Return the project root directory.

    Goal:
        Resolve paths relative to the repository root regardless of CWD.

    Returns:
        The repository root directory as a `Path`.
    """
    # `settings.py` lives under `src/budget_analyser/settings/` (3 parents to repo root).
    return Path(__file__).resolve().parents[3]


def _package_root() -> Path:
    """Return the budget_analyser package root directory.

    Returns:
        The package root directory (src/budget_analyser) as a `Path`.
    """
    # `settings.py` lives under `src/budget_analyser/settings/` (1 parent to package root).
    return Path(__file__).resolve().parents[1]


def _load_dotenv(dotenv_path: Path) -> None:
    """Load environment variables from a `.env` file into `os.environ`.

    Notes:
        - This intentionally behaves like "dotenv" defaults:
          it does not overwrite existing environment variables.
        - Lines starting with `#` are treated as comments.
        - Invalid lines are ignored.

    Args:
        dotenv_path: Path to a `.env` file.
    """
    # Skip if there is no `.env` file.
    if not dotenv_path.exists():
        return

    # Parse each line and populate `os.environ` with default values.
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        # Normalize whitespace.
        line = raw_line.strip()
        # Ignore blanks and comments.
        if not line or line.startswith("#"):
            continue
        # Ignore malformed lines.
        if "=" not in line:
            continue
        # Split only on the first equals so values can contain '='.
        key, value = line.split("=", 1)
        # Clean up extracted key/value.
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # Do not override an existing environment variable.
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    """Strongly-typed runtime configuration.

    Purpose:
        Collect all configuration values in one object to support dependency injection.

    Attributes:
        statement_dir: Directory containing statement CSV files.
        ini_config_path: INI configuration file path.
        description_to_sub_category_path: JSON mapping file for description -> sub_category.
        sub_category_to_category_path: JSON mapping file for sub_category -> category.
        cashflow_to_category_path: JSON mapping file for earnings/expenses -> categories.
        database_path: SQLite database file path for storing transactions.
        log_level: Logging verbosity for the application.
    """

    statement_dir: Path
    ini_config_path: Path
    description_to_sub_category_path: Path
    sub_category_to_category_path: Path
    cashflow_to_category_path: Path
    database_path: Path
    log_level: str = "INFO"


def load_settings() -> Settings:
    """Load application settings from environment (and optional `.env`).

    When ``BUDGET_ANALYSER_DATA_DIR`` is set, all paths are derived from it.
    Individual path env vars are still honoured when the data-dir var is absent.

    Environment variables:
    - BUDGET_ANALYSER_DATA_DIR (takes precedence — sets all paths under one root)
    - BUDGET_ANALYSER_STATEMENT_DIR
    - BUDGET_ANALYSER_INI_CONFIG_PATH
    - BUDGET_ANALYSER_DESCRIPTION_TO_SUB_CATEGORY_PATH
    - BUDGET_ANALYSER_SUB_CATEGORY_TO_CATEGORY_PATH
    - BUDGET_ANALYSER_CASHFLOW_TO_CATEGORY_PATH
    - BUDGET_ANALYSER_DATABASE_PATH
    - BUDGET_ANALYSER_LOG_LEVEL
    """
    root = _project_root()
    pkg_root = _package_root()
    _load_dotenv(root / ".env")

    data_dir_str = os.environ.get("BUDGET_ANALYSER_DATA_DIR", "")
    if data_dir_str:
        data_dir = Path(data_dir_str)
        return Settings(
            statement_dir=data_dir / "statements",
            ini_config_path=data_dir / "config" / "budget_analyser.ini",
            description_to_sub_category_path=data_dir / "mappers" / "description_to_sub_category.json",
            sub_category_to_category_path=data_dir / "mappers" / "sub_category_to_category.json",
            cashflow_to_category_path=data_dir / "mappers" / "cashflow_to_category.json",
            database_path=data_dir / "budget_analyser.db",
            log_level=os.environ.get("BUDGET_ANALYSER_LOG_LEVEL", "INFO"),
        )

    statement_dir = Path(
        os.environ.get(
            "BUDGET_ANALYSER_STATEMENT_DIR",
            str(pkg_root / "data" / "statements"),
        )
    )
    ini_config_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_INI_CONFIG_PATH",
            str(pkg_root / "data" / "config" / "budget_analyser.ini"),
        )
    )
    description_to_sub_category_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_DESCRIPTION_TO_SUB_CATEGORY_PATH",
            str(pkg_root / "data" / "mappers" / "description_to_sub_category.json"),
        )
    )
    sub_category_to_category_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_SUB_CATEGORY_TO_CATEGORY_PATH",
            str(pkg_root / "data" / "mappers" / "sub_category_to_category.json"),
        )
    )
    cashflow_to_category_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_CASHFLOW_TO_CATEGORY_PATH",
            str(pkg_root / "data" / "mappers" / "cashflow_to_category.json"),
        )
    )
    database_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_DATABASE_PATH",
            str(pkg_root / "data" / "budget_analyser.db"),
        )
    )
    log_level = os.environ.get("BUDGET_ANALYSER_LOG_LEVEL", "INFO")

    return Settings(
        statement_dir=statement_dir,
        ini_config_path=ini_config_path,
        description_to_sub_category_path=description_to_sub_category_path,
        sub_category_to_category_path=sub_category_to_category_path,
        cashflow_to_category_path=cashflow_to_category_path,
        database_path=database_path,
        log_level=log_level,
    )
