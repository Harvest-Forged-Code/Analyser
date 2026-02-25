from __future__ import annotations

from pathlib import Path

from budget_analyser.settings.preferences import (
    AppPreferences,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PASSWORD,
    DEFAULT_THEME,
    _hash_password_sha256,
)


def test_password_default_and_update(tmp_path: Path) -> None:
    ini = tmp_path / "budget_analyser.ini"
    # No [app] section yet; should default to DEFAULT_PASSWORD
    prefs = AppPreferences(ini)
    assert prefs.verify_password(DEFAULT_PASSWORD) is True
    assert prefs.verify_password("wrong") is False

    # Update to a new password and verify
    prefs.set_password("newpass1")
    assert prefs.verify_password("newpass1") is True
    assert prefs.verify_password(DEFAULT_PASSWORD) is False


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


def test_new_password_stored_as_pbkdf2(tmp_path: Path) -> None:
    ini = tmp_path / "budget_analyser.ini"
    prefs = AppPreferences(ini)
    prefs.set_password("mysecret")
    stored = prefs.get_password_hash()
    assert stored is not None
    assert stored.startswith("pbkdf2$"), (
        f"Expected pbkdf2 format, got: {stored[:20]}"
    )


def test_legacy_sha256_hash_still_verifies(tmp_path: Path) -> None:
    ini = tmp_path / "budget_analyser.ini"
    # Manually write a legacy sha256 hash to the INI
    legacy_hash = _hash_password_sha256("oldpass")
    import configparser
    parser = configparser.ConfigParser()
    parser.add_section("app")
    parser.set("app", "password_hash", legacy_hash)
    with ini.open("w") as f:
        parser.write(f)

    prefs = AppPreferences(ini)
    assert prefs.verify_password("oldpass") is True
    assert prefs.verify_password("wrongpass") is False


def test_pbkdf2_password_round_trip(tmp_path: Path) -> None:
    ini = tmp_path / "budget_analyser.ini"
    prefs = AppPreferences(ini)
    prefs.set_password("str0ngP@ss!")
    assert prefs.verify_password("str0ngP@ss!") is True
    assert prefs.verify_password("wrong") is False


def test_theme_default_and_round_trip(tmp_path: Path) -> None:
    ini = tmp_path / "budget_analyser.ini"
    prefs = AppPreferences(ini)
    # Default when not set
    assert prefs.get_theme() == DEFAULT_THEME

    # Round-trip valid values
    prefs.set_theme("light")
    assert prefs.get_theme() == "light"
    prefs.set_theme("dark")
    assert prefs.get_theme() == "dark"

    # Invalid should raise
    try:
        prefs.set_theme("blue")
        raised = False
    except ValueError:
        raised = True
    assert raised is True
