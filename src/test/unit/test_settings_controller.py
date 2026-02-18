"""Unit tests for features.settings.controller."""

from __future__ import annotations

import configparser
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from budget_analyser.features.settings.service import (
    SettingsController,
)


@pytest.fixture()
def prefs() -> MagicMock:
    """Create mock AppPreferences."""
    mock = MagicMock()
    mock.get_log_level.return_value = "INFO"
    mock.verify_password.return_value = True
    return mock


@pytest.fixture()
def controller(prefs: MagicMock) -> SettingsController:
    """Create SettingsController with mock prefs."""
    return SettingsController(
        logger=logging.getLogger("test"),
        prefs=prefs,
    )


class TestSettingsController:
    """Tests for SettingsController."""

    def test_get_log_levels(
        self, controller: SettingsController,
    ) -> None:
        levels = controller.get_log_levels()
        assert "DEBUG" in levels
        assert "INFO" in levels
        assert "CRITICAL" in levels

    def test_get_current_log_level(
        self, controller: SettingsController,
    ) -> None:
        assert controller.get_current_log_level() == "INFO"

    def test_apply_valid_log_level(
        self,
        controller: SettingsController,
        prefs: MagicMock,
    ) -> None:
        controller.apply_log_level("DEBUG")
        prefs.set_log_level.assert_called_once_with("DEBUG")

    def test_apply_invalid_log_level(
        self, controller: SettingsController,
    ) -> None:
        with pytest.raises(ValueError, match="Invalid log level"):
            controller.apply_log_level("TRACE")

    def test_verify_password(
        self, controller: SettingsController,
    ) -> None:
        assert controller.verify_password("secret") is True

    def test_change_password_success(
        self,
        controller: SettingsController,
        prefs: MagicMock,
    ) -> None:
        controller.change_password(
            current="old", new="newpass", confirm="newpass",
        )
        prefs.set_password.assert_called_once_with("newpass")

    def test_change_password_wrong_current(
        self,
        controller: SettingsController,
        prefs: MagicMock,
    ) -> None:
        prefs.verify_password.return_value = False
        with pytest.raises(ValueError, match="incorrect"):
            controller.change_password(
                current="wrong", new="newpass", confirm="newpass",
            )

    def test_change_password_too_short(
        self, controller: SettingsController,
    ) -> None:
        with pytest.raises(ValueError, match="at least 6"):
            controller.change_password(
                current="old", new="abc", confirm="abc",
            )

    def test_change_password_mismatch(
        self, controller: SettingsController,
    ) -> None:
        with pytest.raises(ValueError, match="do not match"):
            controller.change_password(
                current="old", new="newpass1", confirm="newpass2",
            )

    def test_get_raw_config_returns_file_content(
        self, prefs: MagicMock,
    ) -> None:
        ini_content = "[app]\nlog_level = INFO\n"
        mock_path = MagicMock(spec=Path)
        mock_path.read_text.return_value = ini_content
        prefs.ini_path = mock_path
        controller = SettingsController(
            logger=logging.getLogger("test"), prefs=prefs,
        )
        assert controller.get_raw_config() == ini_content
        mock_path.read_text.assert_called_once_with(encoding="utf-8")

    def test_update_raw_config_valid_ini_succeeds(
        self, prefs: MagicMock, tmp_path: Path,
    ) -> None:
        ini_file = tmp_path / "test.ini"
        ini_file.write_text("[app]\nlog_level = INFO\n", encoding="utf-8")
        prefs.ini_path = ini_file
        controller = SettingsController(
            logger=logging.getLogger("test"), prefs=prefs,
        )
        controller.update_raw_config(content="[app]\nlog_level = DEBUG\n")
        assert ini_file.read_text(encoding="utf-8") == "[app]\nlog_level = DEBUG\n"

    def test_update_raw_config_invalid_ini_raises_value_error(
        self, prefs: MagicMock, tmp_path: Path,
    ) -> None:
        ini_file = tmp_path / "test.ini"
        ini_file.write_text("", encoding="utf-8")
        prefs.ini_path = ini_file
        controller = SettingsController(
            logger=logging.getLogger("test"), prefs=prefs,
        )
        # ConfigParser actually tolerates most text; use a known bad value
        # that triggers a MissingSectionHeaderError
        with pytest.raises(ValueError, match="Invalid INI syntax"):
            controller.update_raw_config(content="\tinvalid = no section header")

    def test_update_raw_config_creates_backup(
        self, prefs: MagicMock, tmp_path: Path,
    ) -> None:
        original = "[app]\nlog_level = INFO\n"
        ini_file = tmp_path / "config.ini"
        ini_file.write_text(original, encoding="utf-8")
        prefs.ini_path = ini_file
        controller = SettingsController(
            logger=logging.getLogger("test"), prefs=prefs,
        )
        controller.update_raw_config(content="[app]\nlog_level = DEBUG\n")
        backup = tmp_path / "config.ini.bak"
        assert backup.exists()
        assert backup.read_text(encoding="utf-8") == original
