"""Auto-update feature data models.

Frozen dataclasses for GitHub release information and update check results.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReleaseInfo:
    """Information about a GitHub release.

    Attributes:
        tag_name: Git tag (e.g. "v1.2.3").
        version: Cleaned version string without 'v' prefix (e.g. "1.2.3").
        name: Release title.
        body: Release notes (truncated to 2000 chars).
        html_url: URL to the release page on GitHub.
        published_at: ISO 8601 publication timestamp.
    """

    tag_name: str
    version: str
    name: str
    body: str
    html_url: str
    published_at: str


@dataclass(frozen=True)
class UpdateCheckResult:
    """Result of checking for application updates.

    Attributes:
        update_available: Whether a newer version exists.
        current_version: The currently running version.
        latest_version: The latest version on GitHub.
        release: Release details when an update is available.
    """

    update_available: bool
    current_version: str
    latest_version: str
    release: ReleaseInfo | None = None
