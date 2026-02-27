"""Tests for first-launch data seeding."""
from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from budget_analyser.settings.seeding import seed_data_directory


@pytest.fixture()
def bundle_data(tmp_path: Path) -> Path:
    """Create a fake PyInstaller bundle data directory."""
    bundle = tmp_path / "bundle_data"
    (bundle / "mappers").mkdir(parents=True)
    (bundle / "config").mkdir(parents=True)
    (bundle / "mappers" / "description_to_sub_category.json").write_text("{}")
    (bundle / "mappers" / "sub_category_to_category.json").write_text("{}")
    (bundle / "mappers" / "cashflow_to_category.json").write_text("{}")
    (bundle / "config" / "budget_analyser.ini").write_text("[DEFAULT]")
    return bundle


def test_seeds_empty_data_dir(tmp_path: Path, bundle_data: Path) -> None:
    """Empty data dir gets mappers, config, statements, and logs."""
    data_dir = tmp_path / "user_data"
    data_dir.mkdir()

    with patch("budget_analyser.settings.seeding._bundle_data_dir", return_value=bundle_data):
        seed_data_directory(data_dir)

    assert (data_dir / "mappers" / "description_to_sub_category.json").exists()
    assert (data_dir / "config" / "budget_analyser.ini").exists()
    assert (data_dir / "statements").is_dir()
    assert (data_dir / "logs").is_dir()


def test_skips_if_mappers_already_exist(tmp_path: Path, bundle_data: Path) -> None:
    """Existing mappers are not overwritten."""
    data_dir = tmp_path / "user_data"
    (data_dir / "mappers").mkdir(parents=True)
    existing = data_dir / "mappers" / "description_to_sub_category.json"
    existing.write_text('{"custom": true}')

    with patch("budget_analyser.settings.seeding._bundle_data_dir", return_value=bundle_data):
        seed_data_directory(data_dir)

    assert existing.read_text() == '{"custom": true}'


def test_no_op_when_bundle_data_absent(tmp_path: Path) -> None:
    """When not running frozen (dev mode), seeding does nothing."""
    data_dir = tmp_path / "user_data"
    data_dir.mkdir()

    with patch("budget_analyser.settings.seeding._bundle_data_dir", return_value=None):
        seed_data_directory(data_dir)

    assert not (data_dir / "mappers").exists()
