from __future__ import annotations

import logging
from typing import List

from budget_analyser.config.preferences import AppPreferences


class SettingsController:
    """Controller for Settings page actions (no Qt/UI here).

    Responsibilities:
      - Expose available log levels and the current level
      - Apply a new log level (persist + update running logger)
      - Validate and update password via preferences
    """

    def __init__(self, logger: logging.Logger, prefs: AppPreferences) -> None:
        self._logger = logger
        self._prefs = prefs

    # --- Log level ---
    def get_log_levels(self) -> List[str]:
        return ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def get_current_log_level(self) -> str:
        return self._prefs.get_log_level()

    def apply_log_level(self, level: str) -> None:
        import logging as _logging

        if level not in self.get_log_levels():
            raise ValueError(f"Invalid log level: {level}")
        self._prefs.set_log_level(level)
        # Apply immediately to the provided logger
        self._logger.setLevel(getattr(_logging, level))
        self._logger.info("Log level changed to %s via SettingsController", level)

    # --- Password ---
    def verify_password(self, password: str) -> bool:
        return self._prefs.verify_password(password)

    def change_password(self, current: str, new: str, confirm: str) -> None:
        if not self._prefs.verify_password(current):
            raise ValueError("Current password is incorrect.")
        if len(new) < 6:
            raise ValueError("New password must be at least 6 characters long.")
        if new != confirm:
            raise ValueError("New passwords do not match.")

        self._prefs.set_password(new)
        self._logger.info("Password updated via SettingsController")
