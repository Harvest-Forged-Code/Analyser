"""Unit tests for features.settings.controller."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from budget_analyser.features.settings.controller import (
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
