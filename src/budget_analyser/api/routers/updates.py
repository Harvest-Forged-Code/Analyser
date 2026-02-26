"""Updates router for Budget Analyser API.

Provides an endpoint for checking whether a newer application
version is available on GitHub.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from budget_analyser.api.dependencies import get_auto_update_service
from budget_analyser.features.auto_update.service import AutoUpdateService

router = APIRouter(prefix="/api/updates", tags=["updates"])


@router.get("/check")
def check_for_update(
    *,
    service: AutoUpdateService = Depends(get_auto_update_service),
) -> dict:
    """Check whether a newer version is available on GitHub.

    Args:
        service: Injected AutoUpdateService.

    Returns:
        Dict with update_available, current_version, latest_version,
        and optional release object.
    """
    result = service.check_for_update()
    payload: dict = {
        "update_available": result.update_available,
        "current_version": result.current_version,
        "latest_version": result.latest_version,
    }
    if result.release is not None:
        payload["release"] = {
            "tag_name": result.release.tag_name,
            "version": result.release.version,
            "name": result.release.name,
            "body": result.release.body,
            "html_url": result.release.html_url,
            "published_at": result.release.published_at,
        }
    else:
        payload["release"] = None
    return payload
