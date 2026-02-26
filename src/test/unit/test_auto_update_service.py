"""Unit tests for AutoUpdateService.

All tests mock ``urllib.request.urlopen`` so that no real HTTP
requests are made.
"""
from __future__ import annotations

import io
import json
import logging
import time
from unittest.mock import patch, MagicMock

import pytest

from budget_analyser.features.auto_update.service import (
    AutoUpdateService,
    _parse_version,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _github_response(
    *,
    tag_name: str = "v2.0.0",
    name: str = "Release 2.0.0",
    body: str = "Release notes",
    html_url: str = "https://github.com/owner/repo/releases/tag/v2.0.0",
    published_at: str = "2026-02-01T00:00:00Z",
) -> MagicMock:
    """Create a mock urlopen response with JSON payload."""
    payload = json.dumps({
        "tag_name": tag_name,
        "name": name,
        "body": body,
        "html_url": html_url,
        "published_at": published_at,
    }).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = payload
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _make_service(
    current_version: str = "1.0.0",
    cache_ttl: int = 3600,
) -> AutoUpdateService:
    """Create an AutoUpdateService for testing."""
    return AutoUpdateService(
        github_owner="test-owner",
        github_repo="test-repo",
        current_version=current_version,
        cache_ttl_seconds=cache_ttl,
        logger=logging.getLogger("test"),
    )


# ---------------------------------------------------------------------------
# _parse_version
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "version_str, expected",
    [
        ("1.2.3", (1, 2, 3)),
        ("v1.2.3", (1, 2, 3)),
        ("0.0.1", (0, 0, 1)),
        ("10.20.30", (10, 20, 30)),
        ("1.0", (1, 0)),
        ("1", (1,)),
        ("v2", (2,)),
        ("", (0,)),
        ("abc", (0,)),
        ("1.2.3-beta", (1, 2, 3)),
    ],
)
def test_parse_version(version_str: str, expected: tuple[int, ...]) -> None:
    """Version strings are parsed into integer tuples."""
    assert _parse_version(version_str) == expected


# ---------------------------------------------------------------------------
# check_for_update – newer version available
# ---------------------------------------------------------------------------

@patch("budget_analyser.features.auto_update.service.urllib.request.urlopen")
def test_newer_version_available(mock_urlopen: MagicMock) -> None:
    """Returns update_available=True when remote version is newer."""
    mock_urlopen.return_value = _github_response(tag_name="v2.0.0")
    service = _make_service(current_version="1.0.0")

    result = service.check_for_update()

    assert result.update_available is True
    assert result.current_version == "1.0.0"
    assert result.latest_version == "2.0.0"
    assert result.release is not None
    assert result.release.version == "2.0.0"
    assert result.release.html_url == (
        "https://github.com/owner/repo/releases/tag/v2.0.0"
    )


# ---------------------------------------------------------------------------
# check_for_update – no update needed
# ---------------------------------------------------------------------------

@patch("budget_analyser.features.auto_update.service.urllib.request.urlopen")
def test_no_update_when_same_version(mock_urlopen: MagicMock) -> None:
    """Returns update_available=False when versions match."""
    mock_urlopen.return_value = _github_response(tag_name="v1.0.0")
    service = _make_service(current_version="1.0.0")

    result = service.check_for_update()

    assert result.update_available is False
    assert result.release is None


@patch("budget_analyser.features.auto_update.service.urllib.request.urlopen")
def test_no_update_when_local_is_newer(mock_urlopen: MagicMock) -> None:
    """Returns update_available=False when local version is ahead."""
    mock_urlopen.return_value = _github_response(tag_name="v1.0.0")
    service = _make_service(current_version="2.0.0")

    result = service.check_for_update()

    assert result.update_available is False
    assert result.release is None


# ---------------------------------------------------------------------------
# check_for_update – error handling
# ---------------------------------------------------------------------------

@patch("budget_analyser.features.auto_update.service.urllib.request.urlopen")
def test_returns_false_on_network_error(mock_urlopen: MagicMock) -> None:
    """Returns update_available=False when GitHub is unreachable."""
    mock_urlopen.side_effect = OSError("Connection refused")
    service = _make_service()

    result = service.check_for_update()

    assert result.update_available is False
    assert result.current_version == "1.0.0"
    assert result.latest_version == "1.0.0"


@patch("budget_analyser.features.auto_update.service.urllib.request.urlopen")
def test_returns_false_on_http_error(mock_urlopen: MagicMock) -> None:
    """Returns update_available=False on HTTP 404/500 etc."""
    import urllib.error
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="https://api.github.com",
        code=404,
        msg="Not Found",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(b""),
    )
    service = _make_service()

    result = service.check_for_update()

    assert result.update_available is False


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------

@patch("budget_analyser.features.auto_update.service.urllib.request.urlopen")
def test_cache_hit_avoids_second_request(mock_urlopen: MagicMock) -> None:
    """Second call within TTL uses cache (only one HTTP request)."""
    mock_urlopen.return_value = _github_response(tag_name="v2.0.0")
    service = _make_service(current_version="1.0.0")

    result1 = service.check_for_update()
    result2 = service.check_for_update()

    assert result1.update_available is True
    assert result2.update_available is True
    assert mock_urlopen.call_count == 1


@patch("budget_analyser.features.auto_update.service.time.monotonic")
@patch("budget_analyser.features.auto_update.service.urllib.request.urlopen")
def test_cache_expires_after_ttl(
    mock_urlopen: MagicMock,
    mock_monotonic: MagicMock,
) -> None:
    """Expired cache triggers a fresh HTTP request."""
    mock_urlopen.return_value = _github_response(tag_name="v2.0.0")
    # Call sequence: (1) _cached_at after first fetch,
    # (2) _is_cache_valid check in second call,
    # (3) _cached_at after second fetch
    mock_monotonic.side_effect = [0.0, 3601.0, 3601.0]
    service = _make_service(current_version="1.0.0", cache_ttl=3600)

    service.check_for_update()
    service.check_for_update()

    assert mock_urlopen.call_count == 2


# ---------------------------------------------------------------------------
# Release body truncation
# ---------------------------------------------------------------------------

@patch("budget_analyser.features.auto_update.service.urllib.request.urlopen")
def test_body_truncated_at_2000_chars(mock_urlopen: MagicMock) -> None:
    """Release body is truncated to 2000 characters."""
    long_body = "x" * 5000
    mock_urlopen.return_value = _github_response(
        tag_name="v2.0.0", body=long_body,
    )
    service = _make_service(current_version="1.0.0")

    result = service.check_for_update()

    assert result.release is not None
    assert len(result.release.body) == 2000


# ---------------------------------------------------------------------------
# Version comparison edge cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "current, remote, expected",
    [
        ("1.0.0", "1.0.1", True),
        ("1.0.0", "1.1.0", True),
        ("1.9.9", "2.0.0", True),
        ("2.0.0", "1.9.9", False),
        ("1.0.0", "1.0.0", False),
        ("0.1.0", "0.1.1", True),
        ("1.0", "1.0.1", True),
    ],
)
@patch("budget_analyser.features.auto_update.service.urllib.request.urlopen")
def test_version_comparison_edge_cases(
    mock_urlopen: MagicMock,
    current: str,
    remote: str,
    expected: bool,
) -> None:
    """Various version comparison scenarios produce correct results."""
    mock_urlopen.return_value = _github_response(tag_name=f"v{remote}")
    service = _make_service(current_version=current)

    result = service.check_for_update()

    assert result.update_available is expected
