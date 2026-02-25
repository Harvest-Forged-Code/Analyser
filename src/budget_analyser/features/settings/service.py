"""Settings service.

Manages application settings (log level, password, raw INI config).
"""

from __future__ import annotations

import configparser
import logging

from budget_analyser.settings.preferences import AppPreferences


class SettingsService:
    """Service for Settings page actions.

    Responsibilities:
      - Expose available log levels and the current level
      - Apply a new log level (persist + update running logger)
      - Validate and update password via preferences

    Example:
        >>> import logging
        >>> logger = logging.getLogger("budget_analyser")
        >>> svc = SettingsService(logger=logger, prefs=prefs)
        >>> svc.get_current_log_level()
        'INFO'
    """

    def __init__(
        self,
        logger: logging.Logger,
        prefs: AppPreferences,
    ) -> None:
        """Initialize the settings service.

        Args:
            logger: Application logger instance.
            prefs: Application preferences for persisting settings.

        Example:
            >>> import logging
            >>> svc = SettingsService(
            ...     logger=logging.getLogger("budget_analyser"),
            ...     prefs=prefs,
            ... )
        """
        self._logger = logger
        self._prefs = prefs

    def get_log_levels(self) -> list[str]:
        """Return available log level names.

        Returns:
            List of valid log level strings.

        Example:
            >>> svc.get_log_levels()
            ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        """
        return ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def get_current_log_level(self) -> str:
        """Return the current log level name.

        Returns:
            Current log level as a string (e.g. "INFO").

        Example:
            >>> svc.get_current_log_level()
            'INFO'
        """
        return self._prefs.get_log_level()

    def apply_log_level(self, level: str) -> None:
        """Apply a new log level.

        Persists the level to preferences and updates the running
        logger.

        Args:
            level: Log level name (DEBUG, INFO, etc.).

        Raises:
            ValueError: If the level is not valid.

        Example:
            >>> svc.apply_log_level("DEBUG")
        """
        if level not in self.get_log_levels():
            raise ValueError(f"Invalid log level: {level}")
        self._prefs.set_log_level(level)
        self._logger.setLevel(getattr(logging, level))
        self._logger.info(
            "Log level changed to %s via SettingsService",
            level,
        )

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash.

        Args:
            password: Password to verify.

        Returns:
            True if the password matches.

        Example:
            >>> svc.verify_password("my_secret")
            True
        """
        return self._prefs.verify_password(password)

    def change_password(
        self,
        current: str,
        new: str,
        confirm: str,
    ) -> None:
        """Change the application password.

        Validates the current password, enforces minimum length,
        and checks that new and confirm match.

        Args:
            current: Current password for verification.
            new: New password to set (minimum 6 characters).
            confirm: Confirmation of the new password.

        Raises:
            ValueError: If current password is wrong, new password
                is too short, or passwords don't match.

        Example:
            >>> svc.change_password(
            ...     current="old_pass",
            ...     new="new_pass_123",
            ...     confirm="new_pass_123",
            ... )
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
            "Password updated via SettingsService",
        )

    def get_raw_config(self) -> str:
        """Read the raw INI config file content.

        Returns:
            Full content of the INI file as a string.

        Example:
            >>> content = svc.get_raw_config()
            >>> print(content)
            [app]
            log_level = INFO
        """
        return self._prefs.ini_path.read_text(encoding="utf-8")

    def update_raw_config(self, *, content: str) -> None:
        """Validate and write raw INI content to the config file.

        Creates a `.ini.bak` backup before overwriting. Validates
        that the content is parseable INI before saving.

        Args:
            content: Raw INI text to save.

        Raises:
            ValueError: If the content is not valid INI syntax.

        Example:
            >>> svc.update_raw_config(content="[app]\\nlog_level = DEBUG\\n")
        """
        parser = configparser.ConfigParser(interpolation=None)
        try:
            parser.read_string(content)
        except configparser.Error as e:
            raise ValueError(f"Invalid INI syntax: {e}") from e

        backup_path = self._prefs.ini_path.with_suffix(".ini.bak")
        if self._prefs.ini_path.exists():
            backup_path.write_text(
                self._prefs.ini_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        self._prefs.ini_path.write_text(content, encoding="utf-8")
        self._logger.info("INI config updated via SettingsService")


SettingsController = SettingsService
