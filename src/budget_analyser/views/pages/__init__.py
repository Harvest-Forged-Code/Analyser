"""Dashboard pages (one class per file).

Contains QWidget subclasses used by the DashboardWindow's stacked content.
"""

from .yearly_summary_page import YearlySummaryPage
from .earnings_page import EarningsPage
from .expenses_page import ExpensesPage
from .upload_page import UploadPage
from .mapper_page import MapperPage
from .settings_page import SettingsPage
from .payments_page import PaymentsPage
from .recurring_page import RecurringPage
from .cashflow_mapper_page import CashflowMapperPage
from .sub_category_mapper_page import SubCategoryMapperPage
from .cashflow_dashboard_page import CashflowDashboardPage
from .unified_mapper_page import UnifiedMapperPage, ValidationReportTab
from .savings_page import SavingsPage
from .net_worth_page import NetWorthPage

# BudgetGoalsPage is lazily imported to avoid circular dependency
# (it lives in features/budget_goals/page.py but imports from views/pages/_page_base)


def __getattr__(name: str):  # type: ignore[no-untyped-def]
    if name == "BudgetGoalsPage":
        from budget_analyser.features.budget_goals.page import BudgetGoalsPage
        return BudgetGoalsPage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "YearlySummaryPage",
    "EarningsPage",
    "ExpensesPage",
    "PaymentsPage",
    "UploadPage",
    "MapperPage",
    "SettingsPage",
    "BudgetGoalsPage",
    "RecurringPage",
    "CashflowMapperPage",
    "SubCategoryMapperPage",
    "CashflowDashboardPage",
    "UnifiedMapperPage",
    "ValidationReportTab",
    "SavingsPage",
    "NetWorthPage",
]
