"""User preferences persisted in the INI file.

Features supported:
  - Application log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
  - Login password (stored as salted SHA‑256: "sha256$<salt_hex>$<hash_hex>")

Notes:
  - If no password is stored in the INI, the default password is "123456".
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

DEFAULT_PASSWORD = "123456"
DEFAULT_LOG_LEVEL = "INFO"


def _hash_password_sha256(plain: str, *, salt: bytes | None = None) -> str:
    """Return salted SHA-256 hash in the form: sha256$<salt_hex>$<hash_hex>.

    If salt is not provided, a random 16-byte salt is generated.
    """
    if salt is None:
        salt = os.urandom(16)
    h = hashlib.sha256()
    h.update(salt)
    h.update(plain.encode("utf-8"))
    digest = h.hexdigest()
    return f"sha256${salt.hex()}${digest}"


def _verify_password_sha256(plain: str, stored: str) -> bool:
    """Verify a password against a stored salted SHA-256 hash string."""
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
        parser = self._parser()
        level = parser.get(APP_SECTION, KEY_LOG_LEVEL, fallback=DEFAULT_LOG_LEVEL)
        level_up = level.upper().strip()
        return level_up if level_up in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"} else DEFAULT_LOG_LEVEL

    def set_log_level(self, level: str) -> None:
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
        parser = self._parser()
        if not parser.has_section(APP_SECTION):
            return None
        value = parser.get(APP_SECTION, KEY_PASSWORD_HASH, fallback="").strip()
        return value or None

    def verify_password(self, plain: str) -> bool:
        stored = self.get_password_hash()
        if stored:
            return _verify_password_sha256(plain, stored)
        # Fallback to default password when nothing is stored
        return plain == DEFAULT_PASSWORD

    def set_password(self, new_plain: str) -> None:
        """Persist new password hash to the INI."""
        hashed = _hash_password_sha256(new_plain)
        parser = self._parser()
        if not parser.has_section(APP_SECTION):
            parser.add_section(APP_SECTION)
        parser.set(APP_SECTION, KEY_PASSWORD_HASH, hashed)
        with self.ini_path.open("w", encoding="utf-8") as f:
            parser.write(f)
