# Goals Page Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the Budget Goals page from plain tables to a rich dashboard-card UI with summary strips, card grids, radial gauges, and drill-down historical charts.

**Architecture:** Additive backend changes (4 new endpoints, new service functions, new DTOs) + complete frontend page rewrite. No database schema changes. Follows existing vertical slice pattern.

**Tech Stack:** Python/FastAPI (backend), React/TypeScript/Tailwind/Radix UI/Recharts (frontend)

**Design Document:** `docs/plans/2026-02-17-goals-page-redesign-design.md`

---

## Task 1: Backend — Summary and History DTOs

Add new data transfer objects to `models.py` for the summary endpoints and progress history.

**Files:**
- Modify: `src/budget_analyser/features/budget_goals/models.py`
- Test: `src/test/unit/test_budget_goals_service.py`

**Step 1: Add DTOs to models.py**

Add these frozen dataclasses after the existing `BudgetProgress` class:

```python
@dataclass
class BudgetGoalsSummary:
    """Aggregate summary of all budget goals.

    Attributes:
        total_monthly_budget: Sum of all default (ALL) goal limits.
        categories_tracked: Count of unique categories with goals.
        month_overrides: Count of month-specific override entries.
    """

    total_monthly_budget: float
    categories_tracked: int
    month_overrides: int


@dataclass
class EarningsGoalsSummary:
    """Aggregate summary of all earnings goals.

    Attributes:
        total_expected_earnings: Sum of all default (ALL) goal amounts.
        sub_categories_tracked: Count of unique sub-categories with goals.
        month_overrides: Count of month-specific override entries.
    """

    total_expected_earnings: float
    sub_categories_tracked: int
    month_overrides: int


@dataclass
class ProgressSummary:
    """Aggregate progress summary for a single month.

    Attributes:
        on_track_count: Categories under 80% budget.
        warning_count: Categories between 80-100% budget.
        over_budget_count: Categories exceeding 100% budget.
        total_spent: Sum of all category spending.
        total_budget: Sum of all category budget limits.
    """

    on_track_count: int
    warning_count: int
    over_budget_count: int
    total_spent: float
    total_budget: float


@dataclass
class CategoryProgressPoint:
    """A single month's progress data for one category.

    Used to build historical trend charts in the drill-down view.

    Attributes:
        year_month: The month period (format: "YYYY-MM").
        budget_limit: Budget ceiling for that month.
        spent: Actual spending in that month.
        remaining: Budget remaining (budget_limit - spent).
        percentage: Percentage of budget consumed.
        status: Budget status: "under", "warning", or "over".
    """

    year_month: str
    budget_limit: float
    spent: float
    remaining: float
    percentage: float
    status: str
```

**Step 2: Update `__init__.py` exports**

Modify: `src/budget_analyser/features/budget_goals/__init__.py`

Add the new models to `__all__`:

```python
__all__ = [
    "BudgetGoalsController",
    "BudgetGoalsRepository",
    "BudgetGoal",
    "BudgetProgress",
    "EarningsGoal",
    "BudgetGoalsSummary",
    "EarningsGoalsSummary",
    "ProgressSummary",
    "CategoryProgressPoint",
]
```

**Step 3: Commit**

```bash
git add src/budget_analyser/features/budget_goals/models.py src/budget_analyser/features/budget_goals/__init__.py
git commit -S -m "feat(budget_goals): add summary and history DTOs"
```

---

## Task 2: Backend — Summary and History Service Functions

Add pure business logic functions for computing summaries and progress history.

**Files:**
- Test: `src/test/unit/test_budget_goals_service.py`
- Modify: `src/budget_analyser/features/budget_goals/service.py`

**Step 1: Write failing tests for `calculate_budget_goals_summary`**

Add to `src/test/unit/test_budget_goals_service.py`:

```python
from budget_analyser.features.budget_goals.models import (
    BudgetGoalsSummary,
    EarningsGoalsSummary,
    ProgressSummary,
    CategoryProgressPoint,
)
from budget_analyser.features.budget_goals.service import (
    calculate_budget_goals_summary,
    calculate_earnings_goals_summary,
    calculate_progress_summary,
    calculate_category_progress_history,
)


# ==================== calculate_budget_goals_summary ====================


def test_budget_summary_empty_goals() -> None:
    result = calculate_budget_goals_summary(goals=[])
    assert result.total_monthly_budget == 0.0
    assert result.categories_tracked == 0
    assert result.month_overrides == 0


def test_budget_summary_all_defaults_only() -> None:
    goals = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
        BudgetGoal(id=2, category="Transport", monthly_limit=200, year_month="ALL"),
    ]
    result = calculate_budget_goals_summary(goals=goals)
    assert result.total_monthly_budget == 700.0
    assert result.categories_tracked == 2
    assert result.month_overrides == 0


def test_budget_summary_with_overrides() -> None:
    goals = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
        BudgetGoal(id=2, category="Food", monthly_limit=600, year_month="2025-12"),
        BudgetGoal(id=3, category="Transport", monthly_limit=200, year_month="ALL"),
        BudgetGoal(id=4, category="Transport", monthly_limit=250, year_month="2025-01"),
    ]
    result = calculate_budget_goals_summary(goals=goals)
    assert result.total_monthly_budget == 700.0  # Only "ALL" goals
    assert result.categories_tracked == 2
    assert result.month_overrides == 2


# ==================== calculate_earnings_goals_summary ====================


def test_earnings_summary_empty_goals() -> None:
    result = calculate_earnings_goals_summary(goals=[])
    assert result.total_expected_earnings == 0.0
    assert result.sub_categories_tracked == 0
    assert result.month_overrides == 0


def test_earnings_summary_with_overrides() -> None:
    goals = [
        EarningsGoal(id=1, sub_category="Salary", expected_amount=5000, year_month="ALL"),
        EarningsGoal(id=2, sub_category="Salary", expected_amount=5500, year_month="2025-12"),
        EarningsGoal(id=3, sub_category="Bonus", expected_amount=1000, year_month="ALL"),
    ]
    result = calculate_earnings_goals_summary(goals=goals)
    assert result.total_expected_earnings == 6000.0
    assert result.sub_categories_tracked == 2
    assert result.month_overrides == 1


# ==================== calculate_progress_summary ====================


def test_progress_summary_empty() -> None:
    result = calculate_progress_summary(progress_list=[])
    assert result.on_track_count == 0
    assert result.warning_count == 0
    assert result.over_budget_count == 0
    assert result.total_spent == 0.0
    assert result.total_budget == 0.0


def test_progress_summary_mixed_statuses() -> None:
    progress_list = [
        BudgetProgress(category="Food", budget_limit=500, spent=200, remaining=300, percentage=40, status="under"),
        BudgetProgress(category="Transport", budget_limit=200, spent=180, remaining=20, percentage=90, status="warning"),
        BudgetProgress(category="Dining", budget_limit=300, spent=350, remaining=-50, percentage=116.7, status="over"),
    ]
    result = calculate_progress_summary(progress_list=progress_list)
    assert result.on_track_count == 1
    assert result.warning_count == 1
    assert result.over_budget_count == 1
    assert result.total_spent == 730.0
    assert result.total_budget == 1000.0


# ==================== calculate_category_progress_history ====================


def test_category_history_empty_expenses() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
    ]
    result = calculate_category_progress_history(
        category="Food",
        budgets=budgets,
        expenses_df=pd.DataFrame(),
        months=["2025-01", "2025-02"],
    )
    assert len(result) == 2
    assert result[0].year_month == "2025-01"
    assert result[0].spent == 0.0
    assert result[0].budget_limit == 500.0


def test_category_history_with_spending() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
    ]
    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15", "2025-02-10"],
        "amount": [-200, -450],
        "category": ["Food", "Food"],
    })
    result = calculate_category_progress_history(
        category="Food",
        budgets=budgets,
        expenses_df=expenses,
        months=["2025-01", "2025-02"],
    )
    assert len(result) == 2
    assert result[0].spent == 200.0
    assert result[0].status == "under"
    assert result[1].spent == 450.0
    assert result[1].status == "warning"


def test_category_history_month_specific_override() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
        BudgetGoal(id=2, category="Food", monthly_limit=700, year_month="2025-02"),
    ]
    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15", "2025-02-10"],
        "amount": [-200, -450],
        "category": ["Food", "Food"],
    })
    result = calculate_category_progress_history(
        category="Food",
        budgets=budgets,
        expenses_df=expenses,
        months=["2025-01", "2025-02"],
    )
    assert result[0].budget_limit == 500.0  # ALL default
    assert result[1].budget_limit == 700.0  # Month override
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest src/test/unit/test_budget_goals_service.py -v -k "summary or history"`
Expected: FAIL with ImportError (functions don't exist yet)

**Step 3: Implement service functions**

Add to `src/budget_analyser/features/budget_goals/service.py`:

```python
from budget_analyser.features.budget_goals.models import (
    BudgetGoalsSummary,
    CategoryProgressPoint,
    EarningsGoalsSummary,
    ProgressSummary,
)


def calculate_budget_goals_summary(
    *,
    goals: list[BudgetGoal],
) -> BudgetGoalsSummary:
    """Compute aggregate summary statistics for budget goals.

    Args:
        goals: All budget goals from the repository.

    Returns:
        BudgetGoalsSummary with totals and counts.
    """
    default_goals = [g for g in goals if g.year_month == "ALL"]
    override_goals = [g for g in goals if g.year_month != "ALL"]
    unique_categories = {g.category for g in goals}

    return BudgetGoalsSummary(
        total_monthly_budget=sum(g.monthly_limit for g in default_goals),
        categories_tracked=len(unique_categories),
        month_overrides=len(override_goals),
    )


def calculate_earnings_goals_summary(
    *,
    goals: list[EarningsGoal],
) -> EarningsGoalsSummary:
    """Compute aggregate summary statistics for earnings goals.

    Args:
        goals: All earnings goals from the repository.

    Returns:
        EarningsGoalsSummary with totals and counts.
    """
    default_goals = [g for g in goals if g.year_month == "ALL"]
    override_goals = [g for g in goals if g.year_month != "ALL"]
    unique_sub_categories = {g.sub_category for g in goals}

    return EarningsGoalsSummary(
        total_expected_earnings=sum(g.expected_amount for g in default_goals),
        sub_categories_tracked=len(unique_sub_categories),
        month_overrides=len(override_goals),
    )


def calculate_progress_summary(
    *,
    progress_list: list[BudgetProgress],
) -> ProgressSummary:
    """Compute aggregate progress summary from individual category progress.

    Args:
        progress_list: List of BudgetProgress for each category.

    Returns:
        ProgressSummary with status counts and totals.
    """
    on_track = sum(1 for p in progress_list if p.status == "under")
    warning = sum(1 for p in progress_list if p.status == "warning")
    over = sum(1 for p in progress_list if p.status == "over")

    return ProgressSummary(
        on_track_count=on_track,
        warning_count=warning,
        over_budget_count=over,
        total_spent=sum(p.spent for p in progress_list),
        total_budget=sum(p.budget_limit for p in progress_list),
    )


def calculate_category_progress_history(
    *,
    category: str,
    budgets: list[BudgetGoal],
    expenses_df: pd.DataFrame,
    months: list[str],
) -> list[CategoryProgressPoint]:
    """Compute historical progress for a single category across months.

    For each month, finds the applicable budget (month-specific override
    or ALL default) and calculates spending against it.

    Args:
        category: The expense category to track.
        budgets: All budget goals (used to find applicable limits).
        expenses_df: DataFrame with all expense transactions.
        months: List of year-month strings to compute history for.

    Returns:
        List of CategoryProgressPoint, one per month, in order.
    """
    # Build lookup: month -> budget_limit for this category
    default_limit = 0.0
    month_limits: dict[str, float] = {}
    for b in budgets:
        if b.category != category:
            continue
        if b.year_month == "ALL":
            default_limit = b.monthly_limit
        else:
            month_limits[b.year_month] = b.monthly_limit

    # Pre-compute spending by month for this category
    spending_by_month: dict[str, float] = {}
    if not expenses_df.empty and "transaction_date" in expenses_df.columns:
        df = expenses_df.copy()
        df["_ym"] = pd.to_datetime(
            df["transaction_date"], errors="coerce",
        ).dt.strftime("%Y-%m")
        cat_df = df[df["category"] == category] if "category" in df.columns else pd.DataFrame()
        if not cat_df.empty:
            grouped = cat_df.groupby("_ym")["amount"].sum()
            for ym, amount in grouped.items():
                spending_by_month[str(ym)] = abs(float(amount))

    result: list[CategoryProgressPoint] = []
    for ym in months:
        limit = month_limits.get(ym, default_limit)
        spent = spending_by_month.get(ym, 0.0)
        remaining = limit - spent
        percentage = (spent / limit * 100) if limit > 0 else 0.0

        if percentage >= 100:
            status = "over"
        elif percentage >= 80:
            status = "warning"
        else:
            status = "under"

        result.append(CategoryProgressPoint(
            year_month=ym,
            budget_limit=limit,
            spent=spent,
            remaining=remaining,
            percentage=percentage,
            status=status,
        ))

    return result
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest src/test/unit/test_budget_goals_service.py -v`
Expected: ALL PASS

**Step 5: Run full test suite**

Run: `uv run pytest src/test/unit/ -q`
Expected: All tests pass

**Step 6: Commit**

```bash
git add src/budget_analyser/features/budget_goals/service.py src/test/unit/test_budget_goals_service.py
git commit -S -m "feat(budget_goals): add summary and history service functions with tests"
```

---

## Task 3: Backend — Controller Methods

Add new methods to `BudgetGoalsController` for the summary and history endpoints.

**Files:**
- Test: `src/test/unit/test_budget_goals_controller.py`
- Modify: `src/budget_analyser/features/budget_goals/controller.py`

**Step 1: Write failing tests**

Add to `src/test/unit/test_budget_goals_controller.py`:

```python
def test_get_budget_goals_summary(tmp_path):
    """Summary returns correct totals and counts."""
    repo = BudgetGoalsRepository(db_path=tmp_path / "test.db")
    ctrl = BudgetGoalsController(repository=repo)
    ctrl.set_budget("Food", 500, "ALL")
    ctrl.set_budget("Transport", 200, "ALL")
    ctrl.set_budget("Food", 600, "2025-12")

    summary = ctrl.get_budget_goals_summary()
    assert summary.total_monthly_budget == 700.0
    assert summary.categories_tracked == 2
    assert summary.month_overrides == 1


def test_get_earnings_goals_summary(tmp_path):
    """Summary returns correct totals and counts."""
    repo = BudgetGoalsRepository(db_path=tmp_path / "test.db")
    ctrl = BudgetGoalsController(repository=repo)
    ctrl.set_earnings_goal("Salary", 5000, "ALL")
    ctrl.set_earnings_goal("Bonus", 1000, "ALL")
    ctrl.set_earnings_goal("Salary", 5500, "2025-12")

    summary = ctrl.get_earnings_goals_summary()
    assert summary.total_expected_earnings == 6000.0
    assert summary.sub_categories_tracked == 2
    assert summary.month_overrides == 1


def test_get_progress_summary(tmp_path):
    """Progress summary returns correct status counts."""
    repo = BudgetGoalsRepository(db_path=tmp_path / "test.db")
    ctrl = BudgetGoalsController(repository=repo)
    ctrl.set_budget("Food", 500, "ALL")
    ctrl.set_budget("Transport", 200, "ALL")

    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15", "2025-01-15"],
        "amount": [-200, -180],
        "category": ["Food", "Transport"],
    })
    summary = ctrl.get_progress_summary(
        expenses_df=expenses, year_month="2025-01",
    )
    assert summary.on_track_count == 1  # Food at 40%
    assert summary.warning_count == 1   # Transport at 90%
    assert summary.over_budget_count == 0


def test_get_category_progress_history(tmp_path):
    """History returns progress for each month."""
    repo = BudgetGoalsRepository(db_path=tmp_path / "test.db")
    ctrl = BudgetGoalsController(repository=repo)
    ctrl.set_budget("Food", 500, "ALL")

    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15", "2025-02-10"],
        "amount": [-200, -450],
        "category": ["Food", "Food"],
    })
    history = ctrl.get_category_progress_history(
        category="Food",
        expenses_df=expenses,
        months=["2025-01", "2025-02"],
    )
    assert len(history) == 2
    assert history[0].spent == 200.0
    assert history[1].spent == 450.0
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest src/test/unit/test_budget_goals_controller.py -v -k "summary or history"`
Expected: FAIL (methods don't exist yet)

**Step 3: Implement controller methods**

Add to `src/budget_analyser/features/budget_goals/controller.py`:

```python
from budget_analyser.features.budget_goals.models import (
    BudgetGoalsSummary,
    CategoryProgressPoint,
    EarningsGoalsSummary,
    ProgressSummary,
)
from budget_analyser.features.budget_goals.service import (
    calculate_budget_goals_summary,
    calculate_category_progress_history,
    calculate_earnings_goals_summary,
    calculate_progress_summary,
)
```

Add these methods to the `BudgetGoalsController` class:

```python
    # ==================== Summaries ====================

    def get_budget_goals_summary(self) -> BudgetGoalsSummary:
        """Get aggregate summary of all budget goals.

        Returns:
            BudgetGoalsSummary with totals and counts.
        """
        goals = self._repo.get_all_budget_goals()
        return calculate_budget_goals_summary(goals=goals)

    def get_earnings_goals_summary(self) -> EarningsGoalsSummary:
        """Get aggregate summary of all earnings goals.

        Returns:
            EarningsGoalsSummary with totals and counts.
        """
        goals = self._repo.get_all_earnings_goals()
        return calculate_earnings_goals_summary(goals=goals)

    def get_progress_summary(
        self,
        expenses_df: pd.DataFrame,
        year_month: str,
    ) -> ProgressSummary:
        """Get aggregate progress summary for a month.

        Args:
            expenses_df: DataFrame with expense transactions.
            year_month: Month to calculate for (format: "YYYY-MM").

        Returns:
            ProgressSummary with status counts and totals.
        """
        progress = self.calculate_budget_progress(expenses_df, year_month)
        return calculate_progress_summary(progress_list=progress)

    def get_category_progress_history(
        self,
        *,
        category: str,
        expenses_df: pd.DataFrame,
        months: list[str],
    ) -> list[CategoryProgressPoint]:
        """Get historical progress for a single category.

        Args:
            category: The expense category to track.
            expenses_df: DataFrame with all expense transactions.
            months: List of year-month strings to compute history for.

        Returns:
            List of CategoryProgressPoint, one per month.
        """
        budgets = self._repo.get_all_budget_goals()
        return calculate_category_progress_history(
            category=category,
            budgets=budgets,
            expenses_df=expenses_df,
            months=months,
        )
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest src/test/unit/test_budget_goals_controller.py -v`
Expected: ALL PASS

**Step 5: Run full test suite**

Run: `uv run pytest src/test/unit/ -q`
Expected: All tests pass

**Step 6: Commit**

```bash
git add src/budget_analyser/features/budget_goals/controller.py src/test/unit/test_budget_goals_controller.py
git commit -S -m "feat(budget_goals): add summary and history controller methods with tests"
```

---

## Task 4: Backend — API Endpoints and Serializers

Add Pydantic schemas and 4 new FastAPI router endpoints.

**Files:**
- Modify: `src/budget_analyser/api/serializers.py`
- Modify: `src/budget_analyser/api/routers/budget_goals.py`

**Step 1: Add Pydantic schemas**

Add to `src/budget_analyser/api/serializers.py` after `BudgetProgressSchema`:

```python
class BudgetGoalsSummarySchema(BaseModel):
    """Serialized BudgetGoalsSummary."""

    total_monthly_budget: float
    categories_tracked: int
    month_overrides: int


class EarningsGoalsSummarySchema(BaseModel):
    """Serialized EarningsGoalsSummary."""

    total_expected_earnings: float
    sub_categories_tracked: int
    month_overrides: int


class ProgressSummarySchema(BaseModel):
    """Serialized ProgressSummary."""

    on_track_count: int
    warning_count: int
    over_budget_count: int
    total_spent: float
    total_budget: float


class CategoryProgressPointSchema(BaseModel):
    """Serialized CategoryProgressPoint."""

    year_month: str
    budget_limit: float
    spent: float
    remaining: float
    percentage: float
    status: str
```

**Step 2: Add 4 new router endpoints**

Add to `src/budget_analyser/api/routers/budget_goals.py`:

```python
from budget_analyser.api.serializers import (
    BudgetGoalsSummarySchema,
    EarningsGoalsSummarySchema,
    ProgressSummarySchema,
    CategoryProgressPointSchema,
)


@router.get("/summary", response_model=BudgetGoalsSummarySchema)
def get_budget_goals_summary(
    *, controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> BudgetGoalsSummarySchema:
    """Get aggregate summary of all budget goals.

    Args:
        controller: Injected BudgetGoalsController.

    Returns:
        BudgetGoalsSummarySchema with totals and counts.
    """
    s = controller.get_budget_goals_summary()
    return BudgetGoalsSummarySchema(
        total_monthly_budget=s.total_monthly_budget,
        categories_tracked=s.categories_tracked,
        month_overrides=s.month_overrides,
    )


@router.get("/earnings/summary", response_model=EarningsGoalsSummarySchema)
def get_earnings_goals_summary(
    *, controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> EarningsGoalsSummarySchema:
    """Get aggregate summary of all earnings goals.

    Args:
        controller: Injected BudgetGoalsController.

    Returns:
        EarningsGoalsSummarySchema with totals and counts.
    """
    s = controller.get_earnings_goals_summary()
    return EarningsGoalsSummarySchema(
        total_expected_earnings=s.total_expected_earnings,
        sub_categories_tracked=s.sub_categories_tracked,
        month_overrides=s.month_overrides,
    )


@router.get(
    "/progress/{year_month}/summary",
    response_model=ProgressSummarySchema,
)
def get_progress_summary(
    *,
    year_month: str,
    reports: list[MonthlyReports] = Depends(get_reports),
    budget_controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> ProgressSummarySchema:
    """Get aggregate progress summary for a month.

    Args:
        year_month: Year-month string (e.g., "2024-01").
        reports: Injected reports cache.
        budget_controller: Injected BudgetGoalsController.

    Returns:
        ProgressSummarySchema with status counts and totals.

    Raises:
        HTTPException: If month not found.
    """
    import pandas as pd
    period = pd.Period(year_month)
    report = next((r for r in reports if r.month == period), None)

    if not report or report.expenses.empty:
        raise HTTPException(
            status_code=404, detail=f"No expense data for {year_month}",
        )

    s = budget_controller.get_progress_summary(
        expenses_df=report.expenses, year_month=year_month,
    )
    return ProgressSummarySchema(
        on_track_count=s.on_track_count,
        warning_count=s.warning_count,
        over_budget_count=s.over_budget_count,
        total_spent=s.total_spent,
        total_budget=s.total_budget,
    )


@router.get(
    "/progress/history/{category}",
    response_model=list[CategoryProgressPointSchema],
)
def get_category_progress_history(
    *,
    category: str,
    reports: list[MonthlyReports] = Depends(get_reports),
    budget_controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> list[CategoryProgressPointSchema]:
    """Get 12-month progress history for a single category.

    Args:
        category: Expense category name.
        reports: Injected reports cache.
        budget_controller: Injected BudgetGoalsController.

    Returns:
        List of CategoryProgressPointSchema, one per available month.
    """
    import pandas as pd

    if not reports:
        return []

    # Build combined expenses from all reports and available months
    all_expenses = []
    months = []
    for report in sorted(reports, key=lambda r: r.month):
        ym = str(report.month)
        months.append(ym)
        if not report.expenses.empty:
            all_expenses.append(report.expenses)

    combined_expenses = (
        pd.concat(all_expenses, ignore_index=True)
        if all_expenses else pd.DataFrame()
    )

    # Limit to last 12 months
    recent_months = months[-12:]

    history = budget_controller.get_category_progress_history(
        category=category,
        expenses_df=combined_expenses,
        months=recent_months,
    )
    return [
        CategoryProgressPointSchema(
            year_month=p.year_month,
            budget_limit=p.budget_limit,
            spent=p.spent,
            remaining=p.remaining,
            percentage=p.percentage,
            status=p.status,
        )
        for p in history
    ]
```

**Important:** The `/progress/history/{category}` endpoint MUST be registered before `/progress/{year_month}` in the router to avoid FastAPI treating "history" as a `year_month` path parameter. Reorder the existing `get_budget_progress` endpoint to come after the history endpoint.

**Step 3: Run full test suite**

Run: `uv run pytest src/test/unit/ -q`
Expected: All tests pass

**Step 4: Commit**

```bash
git add src/budget_analyser/api/serializers.py src/budget_analyser/api/routers/budget_goals.py
git commit -S -m "feat(budget_goals): add summary and history API endpoints with serializers"
```

---

## Task 5: Frontend — Types and React Query Hooks

Add TypeScript interfaces and React Query hooks for the new endpoints.

**Files:**
- Modify: `src/frontend/src/api/types.ts`
- Modify: `src/frontend/src/api/hooks/use-budget-goals.ts`

**Step 1: Add TypeScript interfaces**

Add to `src/frontend/src/api/types.ts` after `BudgetProgress`:

```typescript
export interface BudgetGoalsSummary {
  total_monthly_budget: number;
  categories_tracked: number;
  month_overrides: number;
}

export interface EarningsGoalsSummary {
  total_expected_earnings: number;
  sub_categories_tracked: number;
  month_overrides: number;
}

export interface ProgressSummary {
  on_track_count: number;
  warning_count: number;
  over_budget_count: number;
  total_spent: number;
  total_budget: number;
}

export interface CategoryProgressPoint {
  year_month: string;
  budget_limit: number;
  spent: number;
  remaining: number;
  percentage: number;
  status: string;
}
```

**Step 2: Add React Query hooks**

Add to `src/frontend/src/api/hooks/use-budget-goals.ts`:

```typescript
import type {
  BudgetGoalsSummary,
  EarningsGoalsSummary,
  ProgressSummary,
  CategoryProgressPoint,
} from "../types";

export function useBudgetGoalsSummary() {
  return useQuery({
    queryKey: ["budget-goals", "summary"],
    queryFn: async () => {
      const response = await apiClient.get<BudgetGoalsSummary>(
        "/budget-goals/summary"
      );
      return response.data;
    },
  });
}

export function useEarningsGoalsSummary() {
  return useQuery({
    queryKey: ["earnings-goals", "summary"],
    queryFn: async () => {
      const response = await apiClient.get<EarningsGoalsSummary>(
        "/budget-goals/earnings/summary"
      );
      return response.data;
    },
  });
}

export function useProgressSummary(yearMonth: string | undefined) {
  return useQuery({
    queryKey: ["budget-goals", "progress", "summary", yearMonth],
    queryFn: async () => {
      const response = await apiClient.get<ProgressSummary>(
        `/budget-goals/progress/${yearMonth}/summary`
      );
      return response.data;
    },
    enabled: !!yearMonth,
  });
}

export function useCategoryProgressHistory(category: string | undefined) {
  return useQuery({
    queryKey: ["budget-goals", "progress", "history", category],
    queryFn: async () => {
      const response = await apiClient.get<CategoryProgressPoint[]>(
        `/budget-goals/progress/history/${category}`
      );
      return response.data;
    },
    enabled: !!category,
  });
}
```

Also update the `useSetBudget` and `useSetEarningsGoal` mutations to also invalidate the summary cache:

```typescript
// In useSetBudget, add:
queryClient.invalidateQueries({ queryKey: ["budget-goals", "summary"] });

// In useDeleteBudget, add:
queryClient.invalidateQueries({ queryKey: ["budget-goals", "summary"] });

// In useSetEarningsGoal, add:
queryClient.invalidateQueries({ queryKey: ["earnings-goals", "summary"] });

// In useDeleteEarningsGoal, add:
queryClient.invalidateQueries({ queryKey: ["earnings-goals", "summary"] });
```

**Step 3: Verify frontend compiles**

Run: `cd src/frontend && npx tsc --noEmit`
Expected: No type errors

**Step 4: Commit**

```bash
git add src/frontend/src/api/types.ts src/frontend/src/api/hooks/use-budget-goals.ts
git commit -S -m "feat(budget_goals): add frontend types and hooks for summary and history endpoints"
```

---

## Task 6: Frontend — Budget Goals Tab Redesign

Replace the table-based Budget Goals tab with summary strip + card grid.

**Files:**
- Modify: `src/frontend/src/pages/budget-goals.tsx`

**Step 1: Replace Budget Goals tab content**

Replace the `<TabsContent value="budget-goals">` section with:

1. **Summary strip** — 3 stat cards in a row using `useBudgetGoalsSummary()` hook
2. **Header row** — "Budget Goals" title + "+ Add Budget Goal" button
3. **Card grid** — `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`

Each card uses the existing `Card`, `CardHeader`, `CardContent` components:
- Category name in `CardTitle`
- `formatCurrency(goal.monthly_limit)` + "/mo" prominently displayed
- `Badge` for year_month scope ("All Months" or specific month)
- Edit (Pencil icon) and Delete (Trash2 icon) buttons in card footer
- If category has overrides (count goals with same category but different year_month), show a small badge like "2 overrides"

Import additions: `Pencil` from lucide-react, `useBudgetGoalsSummary` from hooks.

The Add Goal dialog stays similar but replace the free-text category input with a dropdown populated from existing categories (from budget goals data), and replace the year_month text input with a toggle between "All Months" and a month picker (`Select` component).

**Step 2: Verify frontend compiles**

Run: `cd src/frontend && npx tsc --noEmit`
Expected: No type errors

**Step 3: Manual verification**

Run: `cd src/frontend && npm run tauri:dev`
Verify: Budget Goals tab shows summary strip + card grid, add/edit/delete work correctly.

**Step 4: Commit**

```bash
git add src/frontend/src/pages/budget-goals.tsx
git commit -S -m "feat(budget_goals): redesign Budget Goals tab with summary strip and card grid"
```

---

## Task 7: Frontend — Earnings Goals Tab Redesign

Replace the table-based Earnings Goals tab with summary strip + card grid. Symmetric with Task 6.

**Files:**
- Modify: `src/frontend/src/pages/budget-goals.tsx`

**Step 1: Replace Earnings Goals tab content**

Replace the `<TabsContent value="earnings-goals">` section with:

1. **Summary strip** — 3 stat cards using `useEarningsGoalsSummary()` hook
   - Total Expected Earnings, Sub-categories Tracked, Month Overrides
2. **Card grid** — Same pattern as Budget Goals
   - Sub-category name, expected amount, scope badge, edit/delete buttons

**Step 2: Verify frontend compiles**

Run: `cd src/frontend && npx tsc --noEmit`
Expected: No type errors

**Step 3: Manual verification**

Run: `cd src/frontend && npm run tauri:dev`
Verify: Earnings Goals tab shows summary strip + card grid.

**Step 4: Commit**

```bash
git add src/frontend/src/pages/budget-goals.tsx
git commit -S -m "feat(budget_goals): redesign Earnings Goals tab with summary strip and card grid"
```

---

## Task 8: Frontend — Progress Tab Overview Mode

Redesign the Progress tab with summary cards row and progress cards with radial gauges.

**Files:**
- Modify: `src/frontend/src/pages/budget-goals.tsx`

**Step 1: Add view toggle state**

Add state for the overview/detail toggle:

```typescript
const [progressView, setProgressView] = React.useState<"overview" | "detail">("overview");
const [selectedCategory, setSelectedCategory] = React.useState<string | null>(null);
```

**Step 2: Replace Progress tab content — Overview mode**

Replace the `<TabsContent value="progress">` section:

1. **Top controls row:**
   - Month selector (existing)
   - View toggle: two `Button` variants showing "Overview" | "Detail" (only visible when a category is selected)

2. **Summary cards row** (4 cards in a row) using `useProgressSummary(selectedMonth)`:
   - On Track card (green left border) — `summary.on_track_count` categories
   - Warning card (yellow left border) — `summary.warning_count` categories
   - Over Budget card (red left border) — `summary.over_budget_count` categories
   - Total Spent card — `formatCurrency(summary.total_spent)` of `formatCurrency(summary.total_budget)`

3. **Progress cards grid** (existing `useBudgetProgress` data):
   - Replace the linear progress bar with a `RadialBarChart` from Recharts
   - Each card is clickable — `onClick` sets `selectedCategory` and switches to detail view

Import: `import { RadialBarChart, RadialBar, ResponsiveContainer } from "recharts";`

The radial gauge for each card:
```tsx
<ResponsiveContainer width={80} height={80}>
  <RadialBarChart
    innerRadius="70%"
    outerRadius="100%"
    data={[{ value: Math.min(progress.percentage, 100), fill: gaugeColor }]}
    startAngle={90}
    endAngle={-270}
  >
    <RadialBar dataKey="value" background cornerRadius={5} />
  </RadialBarChart>
</ResponsiveContainer>
```

Where `gaugeColor` is:
- `"#22c55e"` (green) for under 75%
- `"#eab308"` (yellow) for 75-100%
- `"#ef4444"` (red) for over 100%

**Step 3: Verify frontend compiles**

Run: `cd src/frontend && npx tsc --noEmit`
Expected: No type errors

**Step 4: Manual verification**

Run: `cd src/frontend && npm run tauri:dev`
Verify: Progress tab shows summary row + radial gauge cards, clicking a card transitions to detail view.

**Step 5: Commit**

```bash
git add src/frontend/src/pages/budget-goals.tsx
git commit -S -m "feat(budget_goals): redesign Progress tab overview with summary cards and radial gauges"
```

---

## Task 9: Frontend — Progress Tab Detail Mode (Drill-Down)

Add the category drill-down view with line chart and monthly breakdown table.

**Files:**
- Modify: `src/frontend/src/pages/budget-goals.tsx`

**Step 1: Add detail view within Progress tab**

When `progressView === "detail"` and `selectedCategory` is set, render:

1. **Back button:**
   ```tsx
   <Button variant="ghost" onClick={() => { setProgressView("overview"); setSelectedCategory(null); }}>
     <ArrowLeft className="h-4 w-4 mr-2" /> Back to Overview
   </Button>
   ```
   Import: `ArrowLeft` from lucide-react

2. **Category header with status badge**

3. **Line chart** using `useCategoryProgressHistory(selectedCategory)`:
   ```tsx
   import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area, ComposedChart } from "recharts";
   ```

   Use a `ComposedChart` with:
   - X axis: `year_month`
   - Blue `Line` for `spent`
   - Dashed gray `Line` for `budget_limit`
   - `Tooltip` showing month, spent, budget, remaining

4. **Monthly breakdown table** below the chart:
   - Columns: Month, Budget, Spent, Remaining, Status
   - Use the data from `useCategoryProgressHistory`
   - Color-code remaining (green positive, red negative)
   - Status badges

**Step 2: Verify frontend compiles**

Run: `cd src/frontend && npx tsc --noEmit`
Expected: No type errors

**Step 3: Manual verification**

Run: `cd src/frontend && npm run tauri:dev`
Verify: Clicking a progress card drills into the detail view with line chart and table. Back button returns to overview.

**Step 4: Run all backend tests**

Run: `uv run pytest src/test/unit/ -q`
Expected: All tests pass

**Step 5: Commit**

```bash
git add src/frontend/src/pages/budget-goals.tsx
git commit -S -m "feat(budget_goals): add Progress tab drill-down with line chart and monthly table"
```

---

## Task 10: Final Verification and Cleanup

Run all tests, verify no lint errors, ensure everything works end-to-end.

**Step 1: Run all backend unit tests**

Run: `uv run pytest src/test/unit/ -q`
Expected: All tests pass

**Step 2: Run pylint**

Run: `uv run pylint src/budget_analyser/features/budget_goals/`
Expected: No errors (score 10/10 or close)

**Step 3: Run frontend type check**

Run: `cd src/frontend && npx tsc --noEmit`
Expected: No type errors

**Step 4: Manual smoke test**

Run: `cd src/frontend && npm run tauri:dev`
Verify all 3 tabs work:
- Budget Goals: summary strip, card grid, add/edit/delete
- Earnings Goals: summary strip, card grid, add/edit/delete
- Progress: summary row, radial gauges, click drill-down, line chart, back button

**Step 5: Final commit (if any cleanup needed)**

```bash
git add -A
git commit -S -m "chore(budget_goals): cleanup and final verification for goals page redesign"
```
