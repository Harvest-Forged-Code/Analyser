"""Budget burn rate tracking (domain logic).

Backward-compatibility shim: re-exports from features.trends.
New code should import from budget_analyser.features.trends directly.
"""

from budget_analyser.features.trends import (  # pylint: disable=unused-import  # noqa: F401
    BurnRateMetrics,
    CategoryBurnRate,
    BurnRateService,
    calculate_burn_rate,
)
