"""Auto-update service for checking GitHub releases.

Generic, reusable service that checks the GitHub Releases API for
newer versions.  Designed to be decoupled from any GUI framework so
it can be ported to other projects.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request
import urllib.error

from budget_analyser.features.auto_update.models import (
    ReleaseInfo,
    UpdateCheckResult,
)

_MAX_BODY_LENGTH = 2000
_DEFAULT_CACHE_TTL = 3600  # 1 hour


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string into a tuple of integers.

    Strips a leading 'v' prefix and splits on '.'.

    Args:
        version_str: Version string like "1.2.3" or "v1.2.3".

    Returns:
        Tuple of integer components, e.g. (1, 2, 3).
    """
    cleaned = version_str.lstrip("v").strip()
    # Strip pre-release suffix (e.g. "1.2.3-beta" → "1.2.3")
    cleaned = cleaned.split("-", 1)[0]
    parts: list[int] = []
    for part in cleaned.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            break
    return tuple(parts) if parts else (0,)


class AutoUpdateService:  # pylint: disable=too-few-public-methods
    """Check GitHub Releases for newer application versions.

    Uses in-memory caching to respect GitHub's unauthenticated
    rate limit (60 requests/hour).  All errors are caught and
    logged; the service never raises to callers.

    Args:
        github_owner: GitHub repository owner (e.g. "Harvest-Forged-Code").
        github_repo: GitHub repository name (e.g. "Analyser").
        current_version: The currently running application version.
        cache_ttl_seconds: How long to cache a result (default 3600s).
        logger: Optional logger instance.
    """

    def __init__(
        self,
        *,
        github_owner: str,
        github_repo: str,
        current_version: str,
        cache_ttl_seconds: int = _DEFAULT_CACHE_TTL,
        logger: logging.Logger | None = None,
    ) -> None:
        self._owner = github_owner
        self._repo = github_repo
        self._current_version = current_version
        self._cache_ttl = cache_ttl_seconds
        self._logger = logger or logging.getLogger(__name__)

        # In-memory cache
        self._cached_result: UpdateCheckResult | None = None
        self._cached_at: float = 0.0

    def check_for_update(self) -> UpdateCheckResult:
        """Check whether a newer release exists on GitHub.

        Returns a cached result if the cache TTL has not expired.
        On any error the method returns ``update_available=False``
        so that the application is never blocked.

        Returns:
            UpdateCheckResult with version comparison and optional
            release details.
        """
        if self._is_cache_valid():
            self._logger.debug("Returning cached update check result")
            return self._cached_result  # type: ignore[return-value]

        try:
            result = self._fetch_and_compare()
        except Exception:  # pylint: disable=broad-exception-caught
            self._logger.exception("Error checking for updates")
            result = UpdateCheckResult(
                update_available=False,
                current_version=self._current_version,
                latest_version=self._current_version,
            )

        self._cached_result = result
        self._cached_at = time.monotonic()
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_cache_valid(self) -> bool:
        """Return True if the cached result is still fresh."""
        if self._cached_result is None:
            return False
        elapsed = time.monotonic() - self._cached_at
        return elapsed < self._cache_ttl

    def _fetch_and_compare(self) -> UpdateCheckResult:
        """Fetch the latest release from GitHub and compare versions."""
        url = (
            f"https://api.github.com/repos/"
            f"{self._owner}/{self._repo}/releases/latest"
        )
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "BudgetAnalyser-UpdateCheck",
            },
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        tag_name: str = data.get("tag_name", "")
        latest_version = tag_name.lstrip("v").strip()
        body = data.get("body", "") or ""
        if len(body) > _MAX_BODY_LENGTH:
            body = body[:_MAX_BODY_LENGTH]

        release = ReleaseInfo(
            tag_name=tag_name,
            version=latest_version,
            name=data.get("name", "") or "",
            body=body,
            html_url=data.get("html_url", "") or "",
            published_at=data.get("published_at", "") or "",
        )

        current_tuple = _parse_version(self._current_version)
        latest_tuple = _parse_version(latest_version)
        update_available = latest_tuple > current_tuple

        self._logger.info(
            "Update check: current=%s latest=%s available=%s",
            self._current_version,
            latest_version,
            update_available,
        )

        return UpdateCheckResult(
            update_available=update_available,
            current_version=self._current_version,
            latest_version=latest_version,
            release=release if update_available else None,
        )
