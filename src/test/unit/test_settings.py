"""Tests for settings data-dir resolution."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from budget_analyser.settings.settings import load_settings


def test_data_dir_env_var_sets_all_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """BUDGET_ANALYSER_DATA_DIR overrides all individual path settings."""
    monkeypatch.setenv("BUDGET_ANALYSER_DATA_DIR", str(tmp_path))
    # Clear individual overrides so data_dir takes precedence
    for key in [
        "BUDGET_ANALYSER_STATEMENT_DIR",
        "BUDGET_ANALYSER_INI_CONFIG_PATH",
        "BUDGET_ANALYSER_DESCRIPTION_TO_SUB_CATEGORY_PATH",
        "BUDGET_ANALYSER_SUB_CATEGORY_TO_CATEGORY_PATH",
        "BUDGET_ANALYSER_CASHFLOW_TO_CATEGORY_PATH",
        "BUDGET_ANALYSER_DATABASE_PATH",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = load_settings()

    assert settings.statement_dir == tmp_path / "statements"
    assert settings.ini_config_path == tmp_path / "config" / "budget_analyser.ini"
    assert settings.description_to_sub_category_path == tmp_path / "mappers" / "description_to_sub_category.json"
    assert settings.sub_category_to_category_path == tmp_path / "mappers" / "sub_category_to_category.json"
    assert settings.cashflow_to_category_path == tmp_path / "mappers" / "cashflow_to_category.json"
    assert settings.database_path == tmp_path / "budget_analyser.db"


def test_data_dir_absent_uses_existing_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without BUDGET_ANALYSER_DATA_DIR, existing per-path env vars still work."""
    monkeypatch.delenv("BUDGET_ANALYSER_DATA_DIR", raising=False)
    monkeypatch.setenv("BUDGET_ANALYSER_DATABASE_PATH", "/tmp/test.db")

    settings = load_settings()

    assert settings.database_path == Path("/tmp/test.db")
