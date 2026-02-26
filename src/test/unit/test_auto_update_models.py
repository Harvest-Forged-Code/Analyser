"""Unit tests for auto-update feature data models."""
from __future__ import annotations

import pytest

from budget_analyser.features.auto_update.models import (
    ReleaseInfo,
    UpdateCheckResult,
)


# ==================== ReleaseInfo ====================


def test_release_info_creation() -> None:
    """ReleaseInfo stores all fields correctly."""
    info = ReleaseInfo(
        tag_name="v1.2.3",
        version="1.2.3",
        name="Release 1.2.3",
        body="Bug fixes and improvements",
        html_url="https://github.com/owner/repo/releases/tag/v1.2.3",
        published_at="2026-01-15T10:00:00Z",
    )
    assert info.tag_name == "v1.2.3"
    assert info.version == "1.2.3"
    assert info.name == "Release 1.2.3"
    assert info.body == "Bug fixes and improvements"
    assert info.html_url == "https://github.com/owner/repo/releases/tag/v1.2.3"
    assert info.published_at == "2026-01-15T10:00:00Z"


def test_release_info_is_immutable() -> None:
    """ReleaseInfo is a frozen dataclass."""
    info = ReleaseInfo(
        tag_name="v1.0.0",
        version="1.0.0",
        name="First release",
        body="Initial release",
        html_url="https://example.com",
        published_at="2026-01-01T00:00:00Z",
    )
    with pytest.raises(AttributeError):
        info.version = "2.0.0"  # type: ignore[misc]


# ==================== UpdateCheckResult ====================


def test_update_check_result_no_update() -> None:
    """UpdateCheckResult defaults release to None."""
    result = UpdateCheckResult(
        update_available=False,
        current_version="1.0.0",
        latest_version="1.0.0",
    )
    assert result.update_available is False
    assert result.current_version == "1.0.0"
    assert result.latest_version == "1.0.0"
    assert result.release is None


def test_update_check_result_with_release() -> None:
    """UpdateCheckResult stores release when update is available."""
    release = ReleaseInfo(
        tag_name="v2.0.0",
        version="2.0.0",
        name="Major release",
        body="Breaking changes",
        html_url="https://example.com",
        published_at="2026-02-01T00:00:00Z",
    )
    result = UpdateCheckResult(
        update_available=True,
        current_version="1.0.0",
        latest_version="2.0.0",
        release=release,
    )
    assert result.update_available is True
    assert result.release is not None
    assert result.release.version == "2.0.0"


def test_update_check_result_is_immutable() -> None:
    """UpdateCheckResult is a frozen dataclass."""
    result = UpdateCheckResult(
        update_available=False,
        current_version="1.0.0",
        latest_version="1.0.0",
    )
    with pytest.raises(AttributeError):
        result.update_available = True  # type: ignore[misc]
