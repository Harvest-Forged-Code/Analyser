"""Dashboard pages (one class per file).

Contains QWidget subclasses used by the DashboardWindow's stacked content.
"""

from .yearly_summary_page import YearlySummaryPage
from .earnings_page import EarningsPage
from .expenses_page import ExpensesPage
from .upload_page import UploadPage
from .mapper_page import MapperPage
from .settings_page import SettingsPage

__all__ = [
    "YearlySummaryPage",
    "EarningsPage",
    "ExpensesPage",
    "UploadPage",
    "MapperPage",
    "SettingsPage",
]
