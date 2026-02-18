"""Settings router for Budget Analyser API.

Provides endpoints for application settings and preferences.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from budget_analyser.api.dependencies import (
    get_settings_controller,
    get_prefs,
)
from budget_analyser.api.serializers import ChangePasswordRequest
from budget_analyser.features.settings.service import SettingsService
from budget_analyser.settings.preferences import AppPreferences

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/log-levels")
def get_log_levels(
    *, service: SettingsService = Depends(get_settings_controller),
) -> list[str]:
    """Get available log levels.

    Args:
        service: Injected SettingsService.

    Returns:
        List of log level strings.
    """
    return service.get_log_levels()


@router.get("/log-level")
def get_current_log_level(
    *, service: SettingsService = Depends(get_settings_controller),
) -> dict[str, str]:
    """Get the current log level.

    Args:
        service: Injected SettingsService.

    Returns:
        Dict with current log_level.
    """
    return {"log_level": service.get_current_log_level()}


@router.put("/log-level")
def set_log_level(
    *,
    level: str,
    service: SettingsService = Depends(get_settings_controller),
) -> dict[str, str]:
    """Set the application log level.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        service: Injected SettingsService.

    Returns:
        Success message.

    Raises:
        HTTPException: If log level is invalid.
    """
    try:
        service.apply_log_level(level)
        return {"message": f"Log level set to {level}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/change-password")
def change_password(
    *,
    body: ChangePasswordRequest,
    service: SettingsService = Depends(get_settings_controller),
) -> dict[str, str]:
    """Change the login password.

    Args:
        body: ChangePasswordRequest with current, new, and confirmation.
        service: Injected SettingsService.

    Returns:
        Success message.

    Raises:
        HTTPException: If password change fails.
    """
    try:
        service.change_password(
            current_password=body.current,
            new_password=body.new_password,
            confirm_password=body.confirm,
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/theme")
def get_theme(
    *, prefs: AppPreferences = Depends(get_prefs),
) -> dict[str, str]:
    """Get the current UI theme.

    Args:
        prefs: Injected AppPreferences.

    Returns:
        Dict with current theme.
    """
    return {"theme": prefs.get_theme()}


@router.put("/theme")
def set_theme(
    *,
    theme: str,
    prefs: AppPreferences = Depends(get_prefs),
) -> dict[str, str]:
    """Set the UI theme.

    Args:
        theme: Theme name (e.g., "light", "dark").
        prefs: Injected AppPreferences.

    Returns:
        Success message.
    """
    prefs.set_theme(theme)
    return {"message": f"Theme set to {theme}"}
