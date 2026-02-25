"""User preferences persisted in the INI file.

Features supported:
  - Application log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
  - Login password (stored as PBKDF2-HMAC-SHA256:
    "pbkdf2$sha256$<iterations>$<salt_hex>$<hash_hex>")

Notes:
  - Legacy sha256 hashes are still verified for backward compatibility
    but new passwords are always stored using PBKDF2.
  - If no password is stored in the INI, the default password applies.
  - This adapter reads/writes the repository INI at runtime.
"""

from __future__ import annotations

import configparser
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


APP_SECTION = "app"
KEY_LOG_LEVEL = "log_level"
KEY_PASSWORD_HASH = "password_hash"
KEY_THEME = "theme"  # light | dark

DEFAULT_PASSWORD = "BudgetAnalyser2024!"  # Stronger default - users should change this
DEFAULT_LOG_LEVEL = "DEBUG"
DEFAULT_THEME = "dark"

_PBKDF2_ITERATIONS = 600_000


def _hash_password(plain: str, *, salt: bytes | None = None) -> str:
    """Return PBKDF2-HMAC-SHA256 hash: ``pbkdf2$sha256$<iter>$<salt>$<dk>``.

    Uses 600 000 iterations (NIST SP 800-132 recommendation for SHA-256).
    A random 32-byte salt is generated when not provided.

    Args:
        plain: The plaintext password to hash.
        salt: Optional salt bytes; generated randomly if not provided.

    Returns:
        Hash string in the format
        ``pbkdf2$sha256$<iterations>$<salt_hex>$<dk_hex>``.
    """
    if salt is None:
        salt = os.urandom(32)
    dk = hashlib.pbkdf2_hmac(
        "sha256", plain.encode("utf-8"), salt, _PBKDF2_ITERATIONS,
    )
    return f"pbkdf2$sha256${_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def _verify_password(plain: str, stored: str) -> bool:
    """Verify a plaintext password against a stored hash string.

    Supports both the current PBKDF2 format and the legacy SHA-256
    format for backward compatibility with existing stored hashes.

    Args:
        plain: The plaintext password to verify.
        stored: Stored hash in ``pbkdf2$…`` or legacy ``sha256$…`` format.

    Returns:
        True if the password matches the stored hash.
    """
    parts = stored.split("$")
    if parts and parts[0] == "pbkdf2":
        try:
            _, algo, iters_str, salt_hex, dk_hex = parts
        except ValueError:
            return False
        if algo != "sha256":
            return False
        try:
            salt = bytes.fromhex(salt_hex)
            iterations = int(iters_str)
        except ValueError:
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", plain.encode("utf-8"), salt, iterations,
        )
        return dk.hex() == dk_hex
    if parts and parts[0] == "sha256":
        return _verify_password_sha256(plain, stored)
    return False


def _hash_password_sha256(plain: str, *, salt: bytes | None = None) -> str:
    """Return salted SHA-256 hash (legacy format, kept for test compatibility).

    Args:
        plain: The plaintext password to hash.
        salt: Optional salt bytes; generated randomly if not provided.

    Returns:
        Hash string in the format ``sha256$<salt_hex>$<hash_hex>``.
    """
    if salt is None:
        salt = os.urandom(32)
    h = hashlib.sha256()
    h.update(salt)
    h.update(plain.encode("utf-8"))
    digest = h.hexdigest()
    return f"sha256${salt.hex()}${digest}"


def _verify_password_sha256(plain: str, stored: str) -> bool:
    """Verify a password against a stored legacy SHA-256 hash.

    Args:
        plain: The plaintext password to verify.
        stored: The stored hash string in ``sha256$salt$digest`` format.

    Returns:
        True if the password matches the stored hash.
    """
    try:
        algo, salt_hex, digest = stored.split("$", 2)
    except ValueError:
        return False
    if algo.lower() != "sha256":
        return False
    try:
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    return _hash_password_sha256(plain, salt=salt) == f"sha256${salt_hex}${digest}"


@dataclass
class AppPreferences:
    """INI-backed user/application preferences."""

    ini_path: Path

    def _parser(self) -> configparser.ConfigParser:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(self.ini_path, encoding="utf-8")
        return parser

    def get_log_level(self) -> str:
        """Return the configured application log level.

        Returns:
            Uppercase log level string (e.g. "DEBUG", "INFO").
            Falls back to DEFAULT_LOG_LEVEL if not set or invalid.
        """
        parser = self._parser()
        level = parser.get(APP_SECTION, KEY_LOG_LEVEL, fallback=DEFAULT_LOG_LEVEL)
        level_up = level.upper().strip()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        return level_up if level_up in valid_levels else DEFAULT_LOG_LEVEL

    def set_log_level(self, level: str) -> None:
        """Persist the application log level to the INI file.

        Args:
            level: Log level string (DEBUG/INFO/WARNING/ERROR/CRITICAL).

        Raises:
            ValueError: If level is not a valid Python log level.
        """
        level_up = level.upper().strip()
        if level_up not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError(f"Invalid log level: {level}")
        parser = self._parser()
        if not parser.has_section(APP_SECTION):
            parser.add_section(APP_SECTION)
        parser.set(APP_SECTION, KEY_LOG_LEVEL, level_up)
        with self.ini_path.open("w", encoding="utf-8") as f:
            parser.write(f)

    def get_password_hash(self) -> str | None:
        """Return the stored password hash from the INI file.

        Returns:
            The hash string, or None if no password is stored.
        """
        parser = self._parser()
        if not parser.has_section(APP_SECTION):
            return None
        value = parser.get(APP_SECTION, KEY_PASSWORD_HASH, fallback="").strip()
        return value or None

    def verify_password(self, plain: str) -> bool:
        """Verify a plaintext password against the stored hash.

        Falls back to the default password if no hash is stored.

        Args:
            plain: The plaintext password to verify.

        Returns:
            True if the password is correct.
        """
        stored = self.get_password_hash()
        if stored:
            return _verify_password(plain, stored)
        # Fallback to default password when nothing is stored
        return plain == DEFAULT_PASSWORD

    def set_password(self, new_plain: str) -> None:
        """Persist new password hash to the INI.

        Args:
            new_plain: The new plaintext password to store (hashed).
        """
        hashed = _hash_password(new_plain)
        parser = self._parser()
        if not parser.has_section(APP_SECTION):
            parser.add_section(APP_SECTION)
        parser.set(APP_SECTION, KEY_PASSWORD_HASH, hashed)
        with self.ini_path.open("w", encoding="utf-8") as f:
            parser.write(f)

    # ---- Theme preferences ----
    def get_theme(self) -> str:
        """Return current UI theme ("dark" or "light")."""
        parser = self._parser()
        theme = parser.get(APP_SECTION, KEY_THEME, fallback=DEFAULT_THEME).strip().lower()
        return theme if theme in {"dark", "light"} else DEFAULT_THEME

    def set_theme(self, theme: str) -> None:
        """Persist the UI theme ("dark" or "light")."""
        t = theme.strip().lower()
        if t not in {"dark", "light"}:
            raise ValueError(f"Invalid theme: {theme}")
        parser = self._parser()
        if not parser.has_section(APP_SECTION):
            parser.add_section(APP_SECTION)
        parser.set(APP_SECTION, KEY_THEME, t)
        with self.ini_path.open("w", encoding="utf-8") as f:
            parser.write(f)
