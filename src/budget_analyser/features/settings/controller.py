"""Settings controller.

Manages application settings (log level, password).
"""

from __future__ import annotations

import logging

from budget_analyser.settings.preferences import AppPreferences


class SettingsController:
    """Controller for Settings page actions.

    Responsibilities:
      - Expose available log levels and the current level
      - Apply a new log level (persist + update running logger)
      - Validate and update password via preferences
    """

    def __init__(
        self,
        logger: logging.Logger,
        prefs: AppPreferences,
    ) -> None:
        self._logger = logger
        self._prefs = prefs

    def get_log_levels(self) -> list[str]:
        """Return available log level names."""
        return ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def get_current_log_level(self) -> str:
        """Return the current log level name."""
        return self._prefs.get_log_level()

    def apply_log_level(self, level: str) -> None:
        """Apply a new log level.

        Args:
            level: Log level name (DEBUG, INFO, etc.).

        Raises:
            ValueError: If the level is not valid.
        """
        if level not in self.get_log_levels():
            raise ValueError(f"Invalid log level: {level}")
        self._prefs.set_log_level(level)
        self._logger.setLevel(getattr(logging, level))
        self._logger.info(
            "Log level changed to %s via SettingsController",
            level,
        )

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash.

        Args:
            password: Password to verify.

        Returns:
            True if the password matches.
        """
        return self._prefs.verify_password(password)

    def change_password(
        self,
        current: str,
        new: str,
        confirm: str,
    ) -> None:
        """Change the application password.

        Args:
            current: Current password for verification.
            new: New password to set.
            confirm: Confirmation of the new password.

        Raises:
            ValueError: If current password is wrong, new password
                is too short, or passwords don't match.
        """
        if not self._prefs.verify_password(current):
            raise ValueError("Current password is incorrect.")
        if len(new) < 6:
            raise ValueError(
                "New password must be at least 6 characters long.",
            )
        if new != confirm:
            raise ValueError("New passwords do not match.")

        self._prefs.set_password(new)
        self._logger.info(
            "Password updated via SettingsController",
        )
