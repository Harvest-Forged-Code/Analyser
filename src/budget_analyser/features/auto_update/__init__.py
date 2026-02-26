"""Auto-update feature module.

Vertical slice for checking GitHub releases and notifying users
when a newer version of the application is available.
"""

from budget_analyser.features.auto_update.models import (
    ReleaseInfo,
    UpdateCheckResult,
)
from budget_analyser.features.auto_update.service import (
    AutoUpdateService,
)

__all__ = [
    "AutoUpdateService",
    "ReleaseInfo",
    "UpdateCheckResult",
]
