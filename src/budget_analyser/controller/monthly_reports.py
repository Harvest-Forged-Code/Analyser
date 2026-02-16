"""MonthlyReports dataclass used by presentation layer.

Backward-compatibility shim: re-exports from core.models.
New code should import from budget_analyser.core.models directly.
"""

from budget_analyser.core.models import MonthlyReports  # pylint: disable=unused-import  # noqa: F401
