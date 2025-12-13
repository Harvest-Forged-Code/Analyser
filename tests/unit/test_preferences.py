from __future__ import annotations

from pathlib import Path

from budget_analyser.config.preferences import AppPreferences, DEFAULT_LOG_LEVEL


def test_password_default_and_update(tmp_path: Path) -> None:
    ini = tmp_path / "budget_analyser.ini"
    # No [app] section yet; should default to 123456
    prefs = AppPreferences(ini)
    assert prefs.verify_password("123456") is True
    assert prefs.verify_password("wrong") is False

    # Update to a new password and verify
    prefs.set_password("newpass1")
    assert prefs.verify_password("newpass1") is True
    assert prefs.verify_password("123456") is False


def test_log_level_round_trip(tmp_path: Path) -> None:
    ini = tmp_path / "budget_analyser.ini"
    prefs = AppPreferences(ini)
    # Default when not set
    assert prefs.get_log_level() == DEFAULT_LOG_LEVEL

    # Round-trip a valid value
    prefs.set_log_level("DEBUG")
    assert prefs.get_log_level() == "DEBUG"

    # Ensure invalid set raises
    try:
        prefs.set_log_level("INVALID_LEVEL")
        raised = False
    except ValueError:
        raised = True
    assert raised is True
