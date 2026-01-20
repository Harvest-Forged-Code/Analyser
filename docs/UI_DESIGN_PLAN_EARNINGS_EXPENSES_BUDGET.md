# Comprehensive UI Design Plan: Earnings, Expenses, and Budget Goals Pages

**Document Version:** 1.0
**Date:** January 2026
**Author:** Senior Financial Software Architect
**Status:** Design Specification

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [New Reusable Widget Library](#3-new-reusable-widget-library)
4. [Earnings Page Redesign](#4-earnings-page-redesign)
5. [Expenses Page Redesign](#5-expenses-page-redesign)
6. [Budget Goals Page Redesign](#6-budget-goals-page-redesign)
7. [Cross-Page Consistency](#7-cross-page-consistency)
8. [Implementation Phases](#8-implementation-phases)
9. [Technical Specifications](#9-technical-specifications)
10. [Appendices](#appendices)

---

## 1. Executive Summary

This document provides a comprehensive UI design plan for redesigning the three core financial tracking pages in Budget Analyser: Earnings, Expenses, and Budget Goals. The redesign focuses on:

- **Visual Hierarchy**: KPI summary cards at the top for glanceable insights
- **Data Visualization**: Donut charts for distribution, progress bars for budgets
- **Accessibility**: Colorblind-safe palette (blue/orange instead of red/green)
- **Consistency**: Shared component library across all pages
- **User Experience**: Following professional finance app standards (Mint, YNAB, Monarch)

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Accuracy First** | Financial calculations use precise formatting |
| **Glanceable Summaries** | KPI cards show key metrics at a glance |
| **Drill-Down Navigation** | Click from summary to detail views |
| **Colorblind Accessibility** | Blue (#0EA5E9) for income, Orange (#F97316) for expenses |
| **Dark Theme Integration** | All components work with existing purple accent (#8B5CF6) |

---

## 2. Current State Analysis

### 2.1 Existing Architecture

**Page Structure:**
```
src/budget_analyser/views/
    pages/
        _page_base.py          # ModernPageMixin with UI factory methods
        earnings_page.py       # 497 lines, table-focused
        expenses_page.py       # 607 lines, tree + table
        budget_goals_page.py   # 700 lines, tabs with forms
    widgets/
        charts.py              # Line, Bar, Pie, Sparkline widgets
        empty_state.py         # EmptyStateWidget, ConditionalEmptyState
        filter_panel.py        # AdvancedFilterPanel, MultiSelectComboBox
```

**ModernPageMixin Factory Methods:**
- `create_page_header(title, subtitle, icon)` - Page header with emoji icon
- `create_card(title)` - Card container with uppercase title
- `create_controls_row()` - Horizontal control layout
- `create_control_label(text)` - Styled label for form controls
- `create_action_button(text, primary)` - Primary/secondary buttons
- `create_scroll_area()` - Scrollable content container
- `style_combo_box(combo, min_height)` - Combo box styling
- `style_date_edit(date_edit, min_height)` - Date picker styling

**Existing Chart Widgets:**
- `LineChartWidget` - Time-series trends (pyqtgraph)
- `BarChartWidget` - Category comparisons (pyqtgraph)
- `PieChartWidget` - Distribution visualization (QPainter, supports donut)
- `SparklineWidget` - Mini inline charts

**Color Palette (from styles.py):**
- Primary Accent: `#8B5CF6` (Purple)
- Deep Purple: `#7C3AED`
- Light Purple Text: `#DDD6FE`, `#E9D5FF`, `#A78BFA`
- Background Dark: `#000000`, `rgba(18, 18, 20, 0.95)`
- Card Border: `rgba(60, 60, 70, 0.3)`

### 2.2 Current Page Limitations

**Earnings Page:**
- No summary KPI cards
- No income distribution visualization
- Direct jump to table without context
- Missing trend indicators

**Expenses Page:**
- No summary KPI cards
- Tree lacks budget utilization bars
- No category-level progress visualization
- Missing spending insights

**Budget Goals Page:**
- Tab-based layout feels fragmented
- Progress bars lack visual polish
- No savings goal cards
- Missing gamification elements
- No zero-based budgeting view

---

## 3. New Reusable Widget Library

### 3.1 Widget Architecture

```
src/budget_analyser/views/widgets/
    __init__.py
    charts.py                    # Existing
    empty_state.py               # Existing
    filter_panel.py              # Existing
    kpi_card.py                  # NEW - KPI summary cards
    progress_indicator.py        # NEW - Progress bars and rings
    goal_card.py                 # NEW - Savings goal cards
    insight_card.py              # NEW - Smart insights
    budget_row.py                # NEW - Budget allocation row
    category_tree_item.py        # NEW - Enhanced tree items
```

### 3.2 KPI Card Widget

**Purpose:** Display key financial metrics with trend indicators and comparisons.

**ASCII Mockup:**
```
+------------------------------------------+
|  TOTAL INCOME                            |
|                                          |
|  $15,450.00                    [^] +8.5% |
|  (large value)            (trend arrow)  |
|                                          |
|  [==========------] 108%                 |
|  (optional mini progress bar)            |
|                                          |
|  vs. $14,230 last month                  |
|  (comparison context)                    |
+------------------------------------------+
```

**Component Specification:**

```python
@dataclass(frozen=True)
class KPICardData:
    """Data transfer object for KPI card."""

    title: str                      # "TOTAL INCOME"
    value: str                      # "$15,450.00"
    trend_value: str | None = None  # "+8.5%"
    trend_direction: str = "neutral"  # "up", "down", "neutral"
    progress_percent: float | None = None  # 0-100 for progress bar
    comparison_text: str | None = None  # "vs. $14,230 last month"
    accent_color: str = "#8B5CF6"   # Card accent color
    value_color: str | None = None  # Override value color
```

**Widget Class:**

```python
class KPICard(QWidget):
    """Reusable KPI summary card widget."""

    clicked = Signal()  # Emitted when card is clicked

    def __init__(
        self,
        data: KPICardData,
        parent: QWidget | None = None,
    ) -> None: ...

    def update_data(self, data: KPICardData) -> None:
        """Update card with new data."""

    def set_selected(self, selected: bool) -> None:
        """Set card selection state for drill-down."""
```

**Styling:**
```python
CARD_STYLE = """
    QWidget#kpiCard {
        background: rgba(18, 18, 20, 0.95);
        border: 1px solid rgba(60, 60, 70, 0.3);
        border-radius: 18px;
        padding: 20px;
    }
    QWidget#kpiCard:hover {
        border-color: rgba(139, 92, 246, 0.4);
    }
    QLabel#kpiTitle {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        color: #8B5CF6;
        text-transform: uppercase;
    }
    QLabel#kpiValue {
        font-size: 28px;
        font-weight: 700;
        color: #F5F3FF;
        letter-spacing: -0.5px;
    }
    QLabel#kpiTrendUp {
        font-size: 14px;
        font-weight: 600;
        color: #0EA5E9;  /* Blue for positive */
    }
    QLabel#kpiTrendDown {
        font-size: 14px;
        font-weight: 600;
        color: #F97316;  /* Orange for negative */
    }
    QLabel#kpiComparison {
        font-size: 12px;
        color: #9CA3AF;
    }
"""
```

### 3.3 Progress Indicator Widget

**Purpose:** Show budget utilization, goal progress with color-coded states.

**Variants:**

1. **Horizontal Progress Bar** - For budget utilization
2. **Circular Progress Ring** - For goal completion
3. **Milestone Progress Bar** - For goal achievements

**ASCII Mockups:**

```
Horizontal Progress Bar:
+-----------------------------------------------+
| Housing                        $3,550 / $3,800|
| [=====================-------] 93%    $250 left
+-----------------------------------------------+

Circular Progress Ring:
    ╭───────╮
   ╱  78%    ╲
  │  $7,800   │
  │ of $10K   │
   ╲         ╱
    ╰───────╯

Milestone Progress Bar:
[===|====|====|====|----|----|----]
   25%   50%   75%   ^current (62%)
```

**Component Specification:**

```python
@dataclass(frozen=True)
class ProgressData:
    """Data for progress indicator."""

    current: float
    target: float
    label: str = ""
    format_as_currency: bool = True
    show_remaining: bool = True
    milestones: list[float] | None = None  # [25, 50, 75, 100]


class ProgressStatus(Enum):
    """Status based on percentage."""

    HEALTHY = "healthy"     # 0-70%: Teal #10B981
    GOOD = "good"           # 71-90%: Blue #0EA5E9
    WARNING = "warning"     # 91-100%: Amber #F59E0B
    OVER = "over"           # >100%: Orange #F97316

    @classmethod
    def from_percentage(cls, pct: float) -> "ProgressStatus":
        if pct <= 70:
            return cls.HEALTHY
        elif pct <= 90:
            return cls.GOOD
        elif pct <= 100:
            return cls.WARNING
        return cls.OVER
```

**Widget Classes:**

```python
class HorizontalProgressBar(QWidget):
    """Budget utilization progress bar with status colors."""

    def __init__(
        self,
        data: ProgressData,
        *,
        height: int = 8,
        show_labels: bool = True,
        parent: QWidget | None = None,
    ) -> None: ...


class CircularProgressRing(QWidget):
    """Circular progress indicator for goals."""

    def __init__(
        self,
        data: ProgressData,
        *,
        size: int = 120,
        thickness: int = 12,
        parent: QWidget | None = None,
    ) -> None: ...


class MilestoneProgressBar(QWidget):
    """Progress bar with milestone markers."""

    def __init__(
        self,
        data: ProgressData,
        parent: QWidget | None = None,
    ) -> None: ...
```

### 3.4 Goal Card Widget

**Purpose:** Display savings goals with visual progress and actions.

**ASCII Mockup:**

```
+------------------------------------------------------------------+
|  [Icon: Target]                                                   |
|                                                                   |
|  Emergency Fund                              Target: $10,000      |
|                                                                   |
|  [====================--------] 72%                               |
|                                                                   |
|  $7,200 saved                       Est. completion: May 2026     |
|                                                                   |
|  +---------------+ +------------------------------------------+   |
|  | Amount saved  | | Monthly contribution: $300               |   |
|  | this month    | | Months remaining: 10                     |   |
|  | $300          | | Status: On Track                         |   |
|  +---------------+ +------------------------------------------+   |
|                                                                   |
|  [Top Up]  [Edit Goal]  [View History]                           |
+------------------------------------------------------------------+
```

**Component Specification:**

```python
@dataclass(frozen=True)
class GoalData:
    """Data for savings goal card."""

    name: str
    icon: str = "target"  # Emoji or icon name
    target_amount: float = 0.0
    current_amount: float = 0.0
    monthly_contribution: float = 0.0
    target_date: date | None = None
    status: str = "on_track"  # on_track, at_risk, behind, completed
    amount_this_month: float = 0.0


class GoalStatus(Enum):
    """Goal tracking status."""

    ON_TRACK = ("on_track", "#10B981", "checkmark")   # Teal
    AT_RISK = ("at_risk", "#F59E0B", "warning")       # Amber
    BEHIND = ("behind", "#F97316", "alert")           # Orange
    COMPLETED = ("completed", "#FFD700", "star")      # Gold
    PAUSED = ("paused", "#6B7280", "pause")           # Gray


class GoalCard(QWidget):
    """Savings goal card with progress visualization."""

    top_up_clicked = Signal()
    edit_clicked = Signal()
    history_clicked = Signal()

    def __init__(
        self,
        data: GoalData,
        *,
        compact: bool = False,
        parent: QWidget | None = None,
    ) -> None: ...
```

### 3.5 Insight Card Widget

**Purpose:** Display smart financial insights and suggestions.

**ASCII Mockup:**

```
+--------------------------------------------------+
| [lightbulb] INSIGHT                               |
|                                                   |
| You spent 15% more on dining this week compared   |
| to your monthly average.                          |
|                                                   |
| [Set Budget for Dining]  [Dismiss]               |
+--------------------------------------------------+
```

**Component Specification:**

```python
@dataclass(frozen=True)
class InsightData:
    """Data for insight card."""

    icon: str  # Emoji or icon
    category: str  # "INSIGHT", "TIP", "ALERT", "ACHIEVEMENT"
    message: str
    action_text: str | None = None
    action_id: str | None = None
    dismissible: bool = True
    priority: int = 0  # Higher = more important


class InsightCard(QWidget):
    """Smart insight notification card."""

    action_clicked = Signal(str)  # Emits action_id
    dismissed = Signal()

    def __init__(
        self,
        data: InsightData,
        parent: QWidget | None = None,
    ) -> None: ...
```

### 3.6 Budget Allocation Row Widget

**Purpose:** Display category budget with progress bar and status in a table row.

**ASCII Mockup:**

```
| Housing        | $3,800  | $3,550  | $250      | [=====-] OK |
| Food & Dining  | $1,000  | $1,200  | -$200     | [!!!!!!] !! |
```

**Component Specification:**

```python
@dataclass(frozen=True)
class BudgetAllocationData:
    """Data for budget allocation row."""

    category: str
    budget: float
    spent: float

    @property
    def remaining(self) -> float:
        return self.budget - self.spent

    @property
    def percentage(self) -> float:
        return (self.spent / self.budget * 100) if self.budget > 0 else 0

    @property
    def status(self) -> ProgressStatus:
        return ProgressStatus.from_percentage(self.percentage)


class BudgetAllocationRow(QWidget):
    """Widget for budget allocation table row with inline progress."""

    category_clicked = Signal(str)  # Emits category name for drill-down

    def __init__(
        self,
        data: BudgetAllocationData,
        parent: QWidget | None = None,
    ) -> None: ...
```

### 3.7 Enhanced Category Tree Item

**Purpose:** Tree item with inline budget progress bar for Expenses page.

**ASCII Mockup:**

```
[-] Housing                           $3,550.00  42%
    [========--------]

    > Rent                            $2,800.00  33%
    > Utilities                         $450.00   5%
    > Insurance                         $300.00   4%
```

**Component Specification:**

```python
class CategoryTreeItemWidget(QWidget):
    """Custom widget for tree items with progress bars."""

    def __init__(
        self,
        name: str,
        amount: float,
        percentage: float,
        *,
        budget: float | None = None,
        is_parent: bool = False,
        parent: QWidget | None = None,
    ) -> None: ...
```

---

## 4. Earnings Page Redesign

### 4.1 Layout Structure

```
+------------------------------------------------------------------+
|  HEADER                                                          |
|  [Icon] Earnings                                                 |
|  Track income by source with budget comparison                   |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|  KPI SUMMARY CARDS (3 cards in horizontal row)                   |
|  +----------------+ +----------------+ +----------------+        |
|  | TOTAL INCOME   | | VS EXPECTED    | | TOP SOURCE     |        |
|  | $15,450.00     | | +$1,200        | | Salary         |        |
|  | +8.5% vs last  | | 108% of target | | 85% of total   |        |
|  +----------------+ +----------------+ +----------------+        |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|  FILTERS (collapsible)                                           |
|  [View: Monthly v] [Month: Jan 2026 v] [Apply Custom Range]      |
+------------------------------------------------------------------+

+------------------+-----------------------------------------------+
|  INCOME          |  EARNINGS BREAKDOWN                           |
|  DISTRIBUTION    |  +------------------------------------------+ |
|  (Donut Chart)   |  | Source      | Actual   | Expected | Diff | |
|                  |  |-------------|----------|----------|------| |
|  [Donut with     |  | Salary      | $12,000  | $12,000  |  $0  | |
|   center total]  |  | Freelance   | $2,450   | $2,000   | +$450| |
|                  |  | Dividends   | $1,000   | $800     | +$200| |
|                  |  | TOTAL       | $15,450  | $14,800  | +$650| |
|                  |  +------------------------------------------+ |
+------------------+-----------------------------------------------+

+------------------------------------------------------------------+
|  TRANSACTIONS                                                    |
|  +--------------------------------------------------------------+|
|  | Date       | Description          | Amount  | Source         ||
|  |------------|----------------------|---------|----------------||
|  | 2026-01-15 | Salary Deposit       | $6,000  | Salary         ||
|  | 2026-01-10 | Client Project ABC   | $1,200  | Freelance      ||
|  | 2026-01-05 | Dividend Payment     | $500    | Dividends      ||
|  +--------------------------------------------------------------+|
+------------------------------------------------------------------+
```

### 4.2 KPI Cards Specification

**Card 1: Total Income**
```python
KPICardData(
    title="TOTAL INCOME",
    value="$15,450.00",
    trend_value="+8.5%",
    trend_direction="up",
    comparison_text="vs. $14,230 last month",
    accent_color="#0EA5E9",  # Blue for income
)
```

**Card 2: Budget Comparison**
```python
KPICardData(
    title="VS EXPECTED",
    value="+$1,200.00",
    progress_percent=108,
    comparison_text="of monthly target",
    accent_color="#10B981" if positive else "#F97316",
)
```

**Card 3: Top Source**
```python
KPICardData(
    title="TOP INCOME SOURCE",
    value="Salary",
    trend_value="85%",
    trend_direction="neutral",
    comparison_text="of total income",
    accent_color="#8B5CF6",
)
```

### 4.3 Donut Chart Integration

**Placement:** Left side of the breakdown section, 250x250px

**Configuration:**
```python
# In earnings_page.py
self._income_chart = PieChartWidget(donut=True)
self._income_chart.setMinimumSize(250, 250)
self._income_chart.set_legend_visible(False)  # Use table as legend

# Data binding
def _update_income_chart(self, breakdown: list[tuple[str, float]]) -> None:
    labels = [item[0] for item in breakdown]
    values = [item[1] for item in breakdown]
    # Use colorblind-safe palette
    colors = self._get_category_colors(len(labels))
    self._income_chart.set_data(labels, values, colors=colors)
```

**Color Palette for Income Sources:**
```python
INCOME_COLORS = [
    "#0EA5E9",  # Sky Blue - Primary income
    "#8B5CF6",  # Purple - Secondary income
    "#10B981",  # Emerald - Investment income
    "#F59E0B",  # Amber - Other income
    "#6366F1",  # Indigo - Rental income
    "#EC4899",  # Pink - Side income
]
```

### 4.4 Enhanced Summary Table

**Columns:**
| Column | Width | Alignment | Format |
|--------|-------|-----------|--------|
| Source | Stretch | Left | Title case with color indicator |
| Actual | 120px | Right | `$X,XXX.XX` |
| % of Total | 80px | Right | `XX.X%` |
| Expected | 120px | Right | `$X,XXX.XX` |
| Diff | 100px | Right | `+/- $X,XXX.XX` (colored) |
| Diff % | 80px | Right | `+/- XX.X%` (colored) |

**Row Enhancements:**
- Color indicator dot matching donut chart segment
- Click to filter transactions
- Selected row highlighted with left border
- Total row always visible at bottom, bold

### 4.5 Code Changes Required

**File:** `src/budget_analyser/views/pages/earnings_page.py`

```python
# Add imports
from budget_analyser.views.widgets.kpi_card import KPICard, KPICardData
from budget_analyser.views.widgets.charts import PieChartWidget

class EarningsPage(QtWidgets.QWidget):
    def _init_ui(self) -> None:
        # ... existing scroll setup ...

        # Header
        header = ModernPageMixin.create_page_header(...)
        root.addWidget(header)

        # NEW: KPI Cards Row
        kpi_container = self._create_kpi_section()
        root.addWidget(kpi_container)

        # Filters card (existing, refactored)
        filters_card = self._create_filters_section()
        root.addWidget(filters_card)

        # NEW: Distribution section (chart + table)
        distribution_container = self._create_distribution_section()
        root.addWidget(distribution_container, 1)

        # Transactions card (existing)
        transactions_card = self._create_transactions_section()
        root.addWidget(transactions_card, 1)

    def _create_kpi_section(self) -> QWidget:
        """Create KPI summary cards row."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Total Income Card
        self._total_income_card = KPICard(KPICardData(
            title="TOTAL INCOME",
            value="$0.00",
            accent_color="#0EA5E9",
        ))
        layout.addWidget(self._total_income_card)

        # VS Expected Card
        self._vs_expected_card = KPICard(KPICardData(
            title="VS EXPECTED",
            value="$0.00",
        ))
        layout.addWidget(self._vs_expected_card)

        # Top Source Card
        self._top_source_card = KPICard(KPICardData(
            title="TOP SOURCE",
            value="--",
        ))
        layout.addWidget(self._top_source_card)

        return container

    def _create_distribution_section(self) -> QWidget:
        """Create income distribution with chart and table."""
        card, card_layout = ModernPageMixin.create_card("EARNINGS BREAKDOWN")

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(24)

        # Donut chart
        self._income_chart = PieChartWidget(donut=True)
        self._income_chart.setMinimumSize(250, 250)
        self._income_chart.setMaximumWidth(280)
        content_layout.addWidget(self._income_chart)

        # Summary table
        self.summary_table = self._create_summary_table()
        content_layout.addWidget(self.summary_table, 1)

        card_layout.addWidget(content)
        return card
```

---

## 5. Expenses Page Redesign

### 5.1 Layout Structure

```
+------------------------------------------------------------------+
|  HEADER                                                          |
|  [Icon] Expenses                                                 |
|  Track and analyze your spending patterns                        |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|  KPI SUMMARY CARDS (3 cards)                                     |
|  +----------------+ +----------------+ +----------------+        |
|  | TOTAL SPENT    | | VS BUDGET      | | TOP CATEGORY   |        |
|  | $8,450.00      | | Under $550     | | Housing        |        |
|  | -3.2% vs last  | | 94% of budget  | | 42% of total   |        |
|  +----------------+ +----------------+ +----------------+        |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|  BUDGET UTILIZATION (horizontal progress bars)                   |
|  +--------------------------------------------------------------+|
|  | Housing        [=====================-------] 93%  $250 left ||
|  | Food & Dining  [=========================!!!] 120% $200 over ||
|  | Transportation [===============-------------] 65%  $280 left ||
|  | Entertainment  [====================---------] 85%  $75 left ||
|  +--------------------------------------------------------------+|
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|  FILTERS (collapsible)                                           |
|  [View: Monthly v] [Month: Jan 2026 v] [Category: All v]         |
+------------------------------------------------------------------+

+--------------------+---------------------------------------------+
|  SPENDING          |  EXPENSE BREAKDOWN (Tree)                   |
|  BY CATEGORY       |  +----------------------------------------+ |
|  (Donut Chart)     |  | [-] Housing           | $3,550  | 42%  | |
|                    |  |     > Rent            | $2,800  | 33%  | |
|  [Donut with       |  |     > Utilities       | $450    | 5%   | |
|   center total]    |  | [-] Food & Dining     | $1,200  | 14%  | |
|                    |  |     > Groceries       | $800    | 9%   | |
|                    |  |     > Restaurants     | $400    | 5%   | |
|                    |  | [+] Transportation    | $650    | 8%   | |
|                    |  +----------------------------------------+ |
+--------------------+---------------------------------------------+

+------------------------------------------------------------------+
|  TRANSACTIONS                                                    |
|  +--------------------------------------------------------------+|
|  | Date       | Description      | Amount | Category | Sub-cat   ||
|  |------------|------------------|--------|----------|----------||
|  | 2026-01-20 | Whole Foods      | $125   | Food     | Groceries||
|  +--------------------------------------------------------------+|
+------------------------------------------------------------------+
```

### 5.2 KPI Cards Specification

**Card 1: Total Spent**
```python
KPICardData(
    title="TOTAL SPENT",
    value="$8,450.00",
    trend_value="-3.2%",
    trend_direction="down",  # Down spending = positive trend
    comparison_text="vs. $8,730 last month",
    accent_color="#F97316",  # Orange for expenses
    value_color="#F97316",
)
```

**Card 2: Budget Status**
```python
KPICardData(
    title="VS BUDGET",
    value="Under by $550",  # or "Over by $X"
    progress_percent=94,
    comparison_text="of $9,000 budget",
    accent_color="#10B981" if under_budget else "#F97316",
)
```

**Card 3: Top Category**
```python
KPICardData(
    title="TOP CATEGORY",
    value="Housing",
    trend_value="42%",
    trend_direction="neutral",
    comparison_text="of total spending",
    accent_color="#8B5CF6",
)
```

### 5.3 Budget Utilization Section

**NEW Component:** Horizontal budget progress bars for each category.

```python
class BudgetUtilizationSection(QWidget):
    """Section showing budget progress for all categories."""

    category_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._bars: dict[str, HorizontalProgressBar] = {}
        self._init_ui()

    def update_budgets(
        self,
        allocations: list[BudgetAllocationData]
    ) -> None:
        """Update all budget progress bars."""
```

**Layout:**
```
+--------------------------------------------------------------+
| BUDGET UTILIZATION                                            |
+--------------------------------------------------------------+
| Housing           $3,550 / $3,800                            |
| [=====================-------] 93%            $250 remaining |
+--------------------------------------------------------------+
| Food & Dining     $1,200 / $1,000                            |
| [=========================!!!] 120%           $200 over      |
+--------------------------------------------------------------+
```

### 5.4 Enhanced Category Tree

**Enhancements:**
1. Color indicator matching donut chart
2. Inline mini progress bar for budgeted categories
3. Percentage of total column
4. Visual expand/collapse indicators

**Tree Item Structure:**
```
[expand] [color-dot] Category Name    Amount    % of Total    [progress-bar]
```

### 5.5 Code Changes Required

**File:** `src/budget_analyser/views/pages/expenses_page.py`

```python
class ExpensesPage(QtWidgets.QWidget):
    def _init_ui(self) -> None:
        # ... existing scroll setup ...

        # Header
        header = ModernPageMixin.create_page_header(...)
        root.addWidget(header)

        # NEW: KPI Cards Row
        kpi_container = self._create_kpi_section()
        root.addWidget(kpi_container)

        # NEW: Budget Utilization Section
        budget_section = self._create_budget_utilization_section()
        root.addWidget(budget_section)

        # Filters card (existing)
        filters_card = self._create_filters_section()
        root.addWidget(filters_card)

        # Distribution section (chart + tree)
        distribution_container = self._create_distribution_section()
        root.addWidget(distribution_container, 1)

        # Transactions card (existing)
        transactions_card = self._create_transactions_section()
        root.addWidget(transactions_card, 1)

    def _create_budget_utilization_section(self) -> QWidget:
        """Create budget progress bars section."""
        card, card_layout = ModernPageMixin.create_card("BUDGET UTILIZATION")

        self._budget_utilization = BudgetUtilizationSection()
        self._budget_utilization.category_clicked.connect(
            self._on_budget_category_clicked
        )
        card_layout.addWidget(self._budget_utilization)

        return card
```

---

## 6. Budget Goals Page Redesign

### 6.1 Complete Layout Restructure

**Current Issues:**
- Tab-based layout fragments the user experience
- Progress bars lack visual polish
- No savings goal visualization
- Missing zero-based budgeting view

**New Layout:**

```
+------------------------------------------------------------------+
|  HEADER                                                          |
|  [Icon] Budget Goals                                             |
|  Set targets and track your progress toward financial freedom    |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|  KPI SUMMARY CARDS (4 cards)                                     |
|  +------------+ +------------+ +------------+ +------------+     |
|  | MONTHLY    | | REMAINING  | | GOALS      | | SAVINGS    |     |
|  | BUDGET     | | TO SPEND   | | ON TRACK   | | THIS MONTH |     |
|  | $9,000     | | $1,550     | | 3 of 5     | | $800       |     |
|  | 83% used   | | 12 days    | | [***--]    | | +15%       |     |
|  +------------+ +------------+ +------------+ +------------+     |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|  BUDGET TO ZERO (Zero-based budgeting summary)                   |
|  +--------------------------------------------------------------+|
|  | Income this month:                            $8,500          ||
|  | - Assigned to expenses:                      -$7,450          ||
|  | - Assigned to savings goals:                   -$800          ||
|  | ------------------------------------------------------------ ||
|  | Ready to Assign:                               $250           ||
|  |                                                               ||
|  | [Assign to Category v]  [Assign to Savings Goal v]           ||
|  +--------------------------------------------------------------+|
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|  SAVINGS GOALS                                        [+ Add Goal]|
+------------------------------------------------------------------+
|  +---------------------------+  +---------------------------+    |
|  | [Target] Emergency Fund   |  | [Plane] Vacation Fund     |    |
|  | Target: $10,000           |  | Target: $3,000            |    |
|  | [=========------] 72%     |  | [====------------] 33%    |    |
|  | $7,200 saved              |  | $1,000 saved              |    |
|  | Est: May 2026             |  | Est: Aug 2026             |    |
|  | [Top Up]                  |  | [Top Up]                  |    |
|  +---------------------------+  +---------------------------+    |
|                                                                  |
|  +---------------------------+                                   |
|  | [Laptop] New Laptop       |                                   |
|  | Target: $2,000            |                                   |
|  | [===============--] 85%   |                                   |
|  | $1,700 saved              |                                   |
|  | Est: Feb 2026             |                                   |
|  | [Top Up] [Complete]       |                                   |
|  +---------------------------+                                   |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|  BUDGET ALLOCATION BY CATEGORY                                   |
+------------------------------------------------------------------+
|  +--------------------------------------------------------------+|
|  | Category       | Budget  | Spent   | Remaining | Status      ||
|  |----------------|---------|---------|-----------|-------------||
|  | Housing        | $3,800  | $3,550  | $250      | [=====-] OK ||
|  | Food & Dining  | $1,000  | $1,200  | -$200     | [!!!!!!] !! ||
|  | Transportation | $800    | $650    | $150      | [===---] OK ||
|  | Entertainment  | $500    | $450    | $50       | [=====-] OK ||
|  | Savings        | $1,500  | $1,500  | $0        | [======] OK ||
|  +--------------------------------------------------------------+|
|                                                                  |
|  [+ Add Budget]  [Edit Budgets]                                 |
+------------------------------------------------------------------+

+------------------------------------------------------------------+
|  EARNINGS EXPECTATIONS                                           |
+------------------------------------------------------------------+
|  +--------------------------------------------------------------+|
|  | Source         | Expected | Actual  | Diff    | Status       ||
|  |----------------|----------|---------|---------|--------------|
|  | Salary         | $12,000  | $12,000 | $0      | [check] Met  ||
|  | Freelance      | $2,000   | $2,450  | +$450   | [star] +22%  ||
|  | Dividends      | $800     | $1,000  | +$200   | [star] +25%  ||
|  +--------------------------------------------------------------+|
+------------------------------------------------------------------+
```

### 6.2 KPI Cards Specification

**Card 1: Monthly Budget**
```python
KPICardData(
    title="MONTHLY BUDGET",
    value="$9,000",
    progress_percent=83,
    comparison_text="83% used",
)
```

**Card 2: Remaining to Spend**
```python
KPICardData(
    title="REMAINING",
    value="$1,550",
    trend_value="12 days",
    trend_direction="neutral",
    comparison_text="left in month",
)
```

**Card 3: Goals On Track**
```python
KPICardData(
    title="GOALS ON TRACK",
    value="3 of 5",
    comparison_text="savings goals",
)
```

**Card 4: Savings This Month**
```python
KPICardData(
    title="SAVED THIS MONTH",
    value="$800",
    trend_value="+15%",
    trend_direction="up",
    comparison_text="vs. last month",
    accent_color="#10B981",
)
```

### 6.3 Zero-Based Budgeting Section

**Purpose:** YNAB-style "give every dollar a job" interface.

```python
class ZeroBasedBudgetSection(QWidget):
    """Zero-based budgeting summary with assignment actions."""

    assign_to_category_clicked = Signal()
    assign_to_goal_clicked = Signal()

    def update_data(
        self,
        income: float,
        assigned_expenses: float,
        assigned_goals: float,
    ) -> None:
        """Update the zero-based budget display."""
        ready_to_assign = income - assigned_expenses - assigned_goals
        # Update UI
```

### 6.4 Savings Goals Grid

**Layout:** 2-column grid of GoalCard widgets.

```python
class SavingsGoalsGrid(QWidget):
    """Grid of savings goal cards."""

    add_goal_clicked = Signal()
    goal_top_up_clicked = Signal(str)  # goal_id
    goal_edit_clicked = Signal(str)
    goal_complete_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._goals: list[GoalCard] = []
        self._init_ui()

    def update_goals(self, goals: list[GoalData]) -> None:
        """Update the goals display."""
```

### 6.5 Budget Allocation Table

**Enhanced Table Features:**
- Inline progress bars
- Color-coded status indicators
- Click to drill down to Expenses page
- Inline editing for budget amounts

### 6.6 Code Changes Required

**File:** `src/budget_analyser/views/pages/budget_goals_page.py`

Complete rewrite needed. Remove tabs, implement unified layout.

```python
class BudgetGoalsPage(QWidget):
    """Redesigned budget goals page with unified layout."""

    def _init_ui(self) -> None:
        scroll, container = ModernPageMixin.create_scroll_area()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        root = QVBoxLayout(container)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)

        # Header
        header = ModernPageMixin.create_page_header(
            title="Budget Goals",
            subtitle="Set targets and track your progress",
            icon="Goal"
        )
        root.addWidget(header)

        # KPI Cards
        kpi_section = self._create_kpi_section()
        root.addWidget(kpi_section)

        # Zero-Based Budgeting
        zbb_section = self._create_zero_based_section()
        root.addWidget(zbb_section)

        # Savings Goals Grid
        goals_section = self._create_savings_goals_section()
        root.addWidget(goals_section)

        # Budget Allocation Table
        allocation_section = self._create_allocation_section()
        root.addWidget(allocation_section)

        # Earnings Expectations
        earnings_section = self._create_earnings_section()
        root.addWidget(earnings_section)
```

---

## 7. Cross-Page Consistency

### 7.1 Shared Design Tokens

**Typography Scale:**
```python
TYPOGRAPHY = {
    "page_title": {"size": 22, "weight": "bold", "color": "#F5F3FF"},
    "section_title": {"size": 11, "weight": 700, "color": "#8B5CF6", "uppercase": True},
    "card_value": {"size": 28, "weight": 700, "color": "#F5F3FF"},
    "table_header": {"size": 12, "weight": 700, "color": "#DDD6FE"},
    "body_text": {"size": 13, "weight": 500, "color": "#E2E4F0"},
    "caption": {"size": 12, "weight": 400, "color": "#9CA3AF"},
}
```

**Spacing Scale:**
```python
SPACING = {
    "page_padding": 32,
    "section_gap": 24,
    "card_padding": 20,
    "card_gap": 16,
    "element_gap": 12,
    "tight_gap": 8,
}
```

**Color Semantic Tokens:**
```python
COLORS = {
    # Income/Positive
    "income": "#0EA5E9",
    "positive": "#10B981",
    "positive_bg": "rgba(16, 185, 129, 0.15)",

    # Expense/Negative
    "expense": "#F97316",
    "negative": "#EF4444",
    "negative_bg": "rgba(239, 68, 68, 0.15)",

    # Status
    "warning": "#F59E0B",
    "warning_bg": "rgba(245, 158, 11, 0.15)",

    # Brand
    "primary": "#8B5CF6",
    "primary_bg": "rgba(139, 92, 246, 0.15)",

    # Neutral
    "neutral": "#6B7280",
    "muted": "#9CA3AF",
}
```

### 7.2 Navigation Patterns

**Drill-Down Flow:**
```
Budget Goals Page
    |
    +---> [Click category budget] -> Expenses Page (filtered)
    |
    +---> [Click savings goal] -> Goal Detail Modal

Expenses Page
    |
    +---> [Click category] -> Filter transactions
    |
    +---> [Click "Set Budget"] -> Budget Goals Page

Earnings Page
    |
    +---> [Click source] -> Filter transactions
    |
    +---> [Click "Set Expected"] -> Budget Goals Page
```

### 7.3 Shared Component Usage

| Component | Earnings | Expenses | Budget Goals |
|-----------|----------|----------|--------------|
| KPICard | 3 cards | 3 cards | 4 cards |
| PieChartWidget (donut) | Yes | Yes | No |
| HorizontalProgressBar | No | Yes | Yes |
| CircularProgressRing | No | No | In GoalCard |
| GoalCard | No | No | Yes (grid) |
| InsightCard | Future | Future | Future |
| EmptyStateWidget | Yes | Yes | Yes |

### 7.4 Filter Persistence

**Global Filter State:**
```python
@dataclass
class GlobalFilterState:
    """Shared filter state across pages."""

    view_mode: str = "Monthly"  # Monthly, Yearly, Custom
    selected_month: date | None = None
    selected_year: int | None = None
    custom_start: date | None = None
    custom_end: date | None = None
```

When navigating between pages, offer to apply the same time period filter.

---

## 8. Implementation Phases

### Phase 1: Core Widgets (Week 1-2)

**Priority:** High Impact, Foundation for All Pages

**Deliverables:**
1. `kpi_card.py` - KPI summary card widget
2. `progress_indicator.py` - Progress bar widgets
3. Update `charts.py` - Ensure donut chart center text works

**Tasks:**
- [ ] Create `KPICard` widget with all variants
- [ ] Create `HorizontalProgressBar` with status colors
- [ ] Create `CircularProgressRing` for goals
- [ ] Add center text support to `PieChartWidget`
- [ ] Unit tests for new widgets

**Acceptance Criteria:**
- Widgets render correctly in both light and dark themes
- All widgets use design tokens from shared constants
- Unit tests pass with >90% coverage

### Phase 2: Earnings Page Redesign (Week 3)

**Priority:** High Impact, User-Facing

**Deliverables:**
1. KPI cards section
2. Donut chart integration
3. Enhanced summary table

**Tasks:**
- [ ] Add KPI cards row to earnings page
- [ ] Add donut chart for income distribution
- [ ] Enhance summary table with color indicators
- [ ] Connect chart clicks to table filtering
- [ ] Integration tests

### Phase 3: Expenses Page Redesign (Week 4)

**Priority:** High Impact, User-Facing

**Deliverables:**
1. KPI cards section
2. Budget utilization progress bars
3. Donut chart integration
4. Enhanced category tree

**Tasks:**
- [ ] Add KPI cards row
- [ ] Create budget utilization section
- [ ] Add donut chart for spending distribution
- [ ] Enhance tree with progress indicators
- [ ] Integration tests

### Phase 4: Budget Goals Page Redesign (Week 5-6)

**Priority:** High Impact, Complete Rewrite

**Deliverables:**
1. Complete layout restructure
2. Zero-based budgeting section
3. Savings goals grid
4. Budget allocation table

**Tasks:**
- [ ] Create `GoalCard` widget
- [ ] Create `ZeroBasedBudgetSection` widget
- [ ] Create `SavingsGoalsGrid` widget
- [ ] Rewrite `BudgetGoalsPage` with new layout
- [ ] Migrate existing functionality
- [ ] Integration tests

### Phase 5: Cross-Page Features (Week 7)

**Priority:** Medium Impact, Polish

**Deliverables:**
1. Navigation drill-downs
2. Filter state persistence
3. Empty state improvements

**Tasks:**
- [ ] Implement drill-down navigation
- [ ] Add filter state sharing
- [ ] Update empty states for new layouts
- [ ] End-to-end testing

### Phase 6: Advanced Features (Future)

**Priority:** Lower Impact, Nice to Have

**Deliverables:**
1. `InsightCard` widget
2. Gamification badges
3. Achievement celebrations

**Tasks:**
- [ ] Create `InsightCard` widget
- [ ] Add badge/achievement system
- [ ] Add celebration animations
- [ ] AI-powered insights integration

---

## 9. Technical Specifications

### 9.1 File Structure After Implementation

```
src/budget_analyser/views/
    widgets/
        __init__.py               # Export all widgets
        charts.py                 # Existing (enhanced)
        empty_state.py            # Existing
        filter_panel.py           # Existing
        kpi_card.py               # NEW
        progress_indicator.py     # NEW
        goal_card.py              # NEW
        insight_card.py           # NEW (Phase 6)
        budget_utilization.py     # NEW
        savings_goals_grid.py     # NEW
        zero_based_budget.py      # NEW
    pages/
        _page_base.py             # Existing (add new factory methods)
        earnings_page.py          # MODIFIED
        expenses_page.py          # MODIFIED
        budget_goals_page.py      # REWRITTEN
```

### 9.2 New Constants Module

**File:** `src/budget_analyser/views/constants.py`

```python
"""Design tokens and constants for the views layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


# Typography
FONT_SIZE_PAGE_TITLE: Final = 22
FONT_SIZE_SECTION_TITLE: Final = 11
FONT_SIZE_CARD_VALUE: Final = 28
FONT_SIZE_TABLE_HEADER: Final = 12
FONT_SIZE_BODY: Final = 13
FONT_SIZE_CAPTION: Final = 12

# Spacing
SPACING_PAGE_PADDING: Final = 32
SPACING_SECTION_GAP: Final = 24
SPACING_CARD_PADDING: Final = 20
SPACING_CARD_GAP: Final = 16
SPACING_ELEMENT_GAP: Final = 12
SPACING_TIGHT_GAP: Final = 8

# Colors - Semantic
COLOR_INCOME: Final = "#0EA5E9"       # Sky Blue
COLOR_EXPENSE: Final = "#F97316"       # Orange
COLOR_POSITIVE: Final = "#10B981"      # Emerald
COLOR_NEGATIVE: Final = "#EF4444"      # Red
COLOR_WARNING: Final = "#F59E0B"       # Amber
COLOR_PRIMARY: Final = "#8B5CF6"       # Purple
COLOR_NEUTRAL: Final = "#6B7280"       # Gray
COLOR_MUTED: Final = "#9CA3AF"         # Light Gray

# Colors - Backgrounds (with alpha)
COLOR_POSITIVE_BG: Final = "rgba(16, 185, 129, 0.15)"
COLOR_NEGATIVE_BG: Final = "rgba(239, 68, 68, 0.15)"
COLOR_WARNING_BG: Final = "rgba(245, 158, 11, 0.15)"
COLOR_PRIMARY_BG: Final = "rgba(139, 92, 246, 0.15)"

# Chart color palettes
INCOME_CHART_COLORS: Final = [
    "#0EA5E9",  # Sky Blue
    "#8B5CF6",  # Purple
    "#10B981",  # Emerald
    "#F59E0B",  # Amber
    "#6366F1",  # Indigo
    "#EC4899",  # Pink
]

EXPENSE_CHART_COLORS: Final = [
    "#F97316",  # Orange
    "#8B5CF6",  # Purple
    "#0EA5E9",  # Sky Blue
    "#10B981",  # Emerald
    "#EF4444",  # Red
    "#F59E0B",  # Amber
]

# Component sizes
KPI_CARD_MIN_HEIGHT: Final = 100
KPI_CARD_MIN_WIDTH: Final = 200
PROGRESS_BAR_HEIGHT: Final = 8
DONUT_CHART_SIZE: Final = 250
GOAL_CARD_MIN_WIDTH: Final = 280


@dataclass(frozen=True)
class ProgressThresholds:
    """Thresholds for progress status colors."""

    healthy_max: float = 70.0
    good_max: float = 90.0
    warning_max: float = 100.0
    # Above warning_max = over
```

### 9.3 Controller Layer Updates

The controller layer needs to provide additional data for the new UI components.

**New Methods Needed:**

```python
# EarningsStatsController
class EarningsStatsController:
    def kpi_summary(self, period: Period) -> EarningsKPISummary:
        """Get KPI data for earnings page."""

    def income_distribution(self, period: Period) -> list[tuple[str, float]]:
        """Get income breakdown for donut chart."""

    def top_income_source(self, period: Period) -> tuple[str, float, float]:
        """Get top income source name, amount, percentage."""


# ExpensesStatsController
class ExpensesStatsController:
    def kpi_summary(self, period: Period) -> ExpensesKPISummary:
        """Get KPI data for expenses page."""

    def spending_distribution(self, period: Period) -> list[tuple[str, float]]:
        """Get spending breakdown for donut chart."""

    def budget_utilization(
        self, period: Period
    ) -> list[BudgetAllocationData]:
        """Get budget vs actual for all categories."""


# BudgetController
class BudgetController:
    def zero_based_summary(self, period: Period) -> ZeroBasedSummary:
        """Get zero-based budgeting summary."""

    def savings_goals_summary(self) -> list[GoalData]:
        """Get all savings goals with progress."""
```

### 9.4 Testing Requirements

**Unit Tests:**
- Each new widget has dedicated test file
- Test all visual states (normal, hover, selected)
- Test data binding and updates
- Test signal emissions

**Integration Tests:**
- Test page rendering with sample data
- Test drill-down navigation
- Test filter application

**Visual Regression Tests:**
- Screenshot comparison for key states
- Both light and dark themes

---

## Appendices

### Appendix A: Color Reference

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Sky Blue | #0EA5E9 | 14, 165, 233 | Income, positive trends |
| Orange | #F97316 | 249, 115, 22 | Expenses, negative amounts |
| Emerald | #10B981 | 16, 185, 129 | Success, under budget |
| Amber | #F59E0B | 245, 158, 11 | Warning, near limit |
| Red | #EF4444 | 239, 68, 68 | Alert, over budget |
| Purple | #8B5CF6 | 139, 92, 246 | Primary accent |
| Gray | #6B7280 | 107, 114, 128 | Neutral, muted |

### Appendix B: Component Size Reference

| Component | Min Height | Min Width | Max Width |
|-----------|-----------|-----------|-----------|
| KPI Card | 100px | 200px | 280px |
| Progress Bar | 8px | - | - |
| Donut Chart | 250px | 250px | 300px |
| Goal Card | 180px | 280px | 340px |
| Action Button | 44px | 100px | - |
| Table Row | 40px | - | - |

### Appendix C: Accessibility Checklist

- [ ] All text meets WCAG 2.1 AA contrast ratio (4.5:1 for normal text)
- [ ] Color is not the only indicator of status (icons/text accompany color)
- [ ] Focus indicators are visible for keyboard navigation
- [ ] Interactive elements have minimum 44x44px touch targets
- [ ] Screen reader labels provided for all interactive elements
- [ ] Charts have text alternatives in tooltips

### Appendix D: Migration Notes

**Earnings Page Migration:**
1. Keep existing controller interface
2. Add new UI sections above existing content
3. Refactor summary table to use new column structure
4. Add donut chart alongside table

**Expenses Page Migration:**
1. Keep existing tree and table functionality
2. Add KPI cards and budget utilization above
3. Enhance tree items with progress indicators
4. Add donut chart alongside tree

**Budget Goals Page Migration:**
1. Complete rewrite - no tab structure
2. Migrate data from existing controller
3. New unified layout
4. Keep existing budget/earnings goal data models

---

*End of Design Plan*