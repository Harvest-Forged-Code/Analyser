from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    statement_dir: Path
    ini_config_path: Path
    description_to_sub_category_path: Path
    sub_category_to_category_path: Path
    log_level: str = "INFO"


def load_settings() -> Settings:
    """Load app settings from environment (and optional .env).

    Environment variables:
    - BUDGET_ANALYSER_STATEMENT_DIR
    - BUDGET_ANALYSER_INI_CONFIG_PATH
    - BUDGET_ANALYSER_DESCRIPTION_TO_SUB_CATEGORY_PATH
    - BUDGET_ANALYSER_SUB_CATEGORY_TO_CATEGORY_PATH
    - BUDGET_ANALYSER_LOG_LEVEL
    """

    root = _project_root()
    _load_dotenv(root / ".env")

    statement_dir = Path(
        os.environ.get(
            "BUDGET_ANALYSER_STATEMENT_DIR",
            str(root / "resources" / "statements"),
        )
    )
    ini_config_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_INI_CONFIG_PATH",
            str(root / "config" / "budget_analyser.ini"),
        )
    )

    description_to_sub_category_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_DESCRIPTION_TO_SUB_CATEGORY_PATH",
            str(root / "resources" / "mappers" / "description_to_sub_category.json"),
        )
    )
    sub_category_to_category_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_SUB_CATEGORY_TO_CATEGORY_PATH",
            str(root / "resources" / "mappers" / "sub_category_to_category.json"),
        )
    )

    log_level = os.environ.get("BUDGET_ANALYSER_LOG_LEVEL", "INFO")

    return Settings(
        statement_dir=statement_dir,
        ini_config_path=ini_config_path,
        description_to_sub_category_path=description_to_sub_category_path,
        sub_category_to_category_path=sub_category_to_category_path,
        log_level=log_level,
    )
