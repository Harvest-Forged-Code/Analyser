"""Settings controller.

Backward-compatibility shim: re-exports from features.settings.
New code should import from budget_analyser.features.settings directly.
"""

from budget_analyser.features.settings import (  # pylint: disable=unused-import  # noqa: F401
    SettingsController,
)
