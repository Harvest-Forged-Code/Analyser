"""Authentication router for Budget Analyser API.

Provides login endpoint for password verification.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from budget_analyser.api.dependencies import get_settings_controller
from budget_analyser.api.serializers import LoginRequest
from budget_analyser.features.settings.service import SettingsService as SettingsController

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(
    *,
    body: LoginRequest,
    controller: SettingsController = Depends(get_settings_controller),
) -> dict[str, bool | str]:
    """Verify password and authenticate user.

    Args:
        body: Login request containing password.
        controller: Injected SettingsController.

    Returns:
        Dict with success status and message.

    Raises:
        HTTPException: If password verification fails.
    """
    if controller.verify_password(body.password):
        return {"success": True, "message": "Authentication successful"}
    raise HTTPException(status_code=401, detail="Invalid password")
