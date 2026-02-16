"""Budget Goals Page - backward-compatibility shim.

Re-exports BudgetGoalsPage from the budget_goals feature slice.
New code should import from budget_analyser.features.budget_goals.page.

Note: This file is not imported by views/pages/__init__.py to avoid
circular imports. The __init__.py imports directly from the feature module.
"""


def __getattr__(name: str):  # type: ignore[no-untyped-def]
    """Lazy import to avoid circular dependency."""
    if name == "BudgetGoalsPage":
        from budget_analyser.features.budget_goals.page import BudgetGoalsPage
        return BudgetGoalsPage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
