"""Spending pattern analysis (domain logic).

Purpose:
    Analyze spending patterns to identify:
    - Pareto analysis (80/20 rule for categories)
    - Day-of-week spending patterns
    - Anomaly detection (outlier transactions)
    - Savings rate trends

Helps users understand their spending behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

import pandas as pd
import numpy as np


class DayOfWeek(Enum):
    """Days of the week."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    @classmethod
    def from_int(cls, day: int) -> DayOfWeek:
        """Convert integer (0=Monday) to DayOfWeek."""
        return cls(day)


@dataclass(frozen=True)
class ParetoItem:
    """A single item in Pareto analysis.

    Attributes:
        category: Category name.
        amount: Total amount for this category.
        percentage: Percentage of total spending.
        cumulative_percentage: Running cumulative percentage.
        is_top_80: Whether this category is in the top 80% of spending.
    """

    category: str
    amount: float
    percentage: float
    cumulative_percentage: float
    is_top_80: bool


@dataclass
class ParetoAnalysis:
    """Pareto (80/20) analysis result.

    Attributes:
        items: List of ParetoItem sorted by amount descending.
        total_amount: Total spending across all categories.
        top_80_count: Number of categories comprising 80% of spending.
        top_80_categories: Categories in the top 80%.
    """

    items: list[ParetoItem] = field(default_factory=list)
    total_amount: float = 0.0

    @property
    def top_80_count(self) -> int:
        """Number of categories in top 80%."""
        return sum(1 for item in self.items if item.is_top_80)

    @property
    def top_80_categories(self) -> list[str]:
        """Categories comprising top 80% of spending."""
        return [item.category for item in self.items if item.is_top_80]

    @property
    def concentration_ratio(self) -> float:
        """Ratio of top 80% categories to total categories."""
        if not self.items:
            return 0.0
        return self.top_80_count / len(self.items)


@dataclass(frozen=True)
class DayPattern:
    """Spending pattern for a day of the week.

    Attributes:
        day: Day of the week.
        total_amount: Total spending on this day.
        transaction_count: Number of transactions.
        average_transaction: Average transaction amount.
        percentage_of_week: Percentage of weekly spending.
    """

    day: DayOfWeek
    total_amount: float
    transaction_count: int
    average_transaction: float
    percentage_of_week: float


@dataclass
class WeeklyPattern:
    """Weekly spending pattern analysis.

    Attributes:
        day_patterns: Spending data for each day.
        highest_day: Day with most spending.
        lowest_day: Day with least spending.
        weekend_percentage: Percentage of spending on weekends.
    """

    day_patterns: list[DayPattern] = field(default_factory=list)

    @property
    def highest_day(self) -> DayOfWeek | None:
        """Day with highest spending."""
        if not self.day_patterns:
            return None
        return max(self.day_patterns, key=lambda p: p.total_amount).day

    @property
    def lowest_day(self) -> DayOfWeek | None:
        """Day with lowest spending."""
        if not self.day_patterns:
            return None
        # Filter out days with zero spending
        active_days = [p for p in self.day_patterns if p.total_amount > 0]
        if not active_days:
            return None
        return min(active_days, key=lambda p: p.total_amount).day

    @property
    def weekend_percentage(self) -> float:
        """Percentage of spending on weekends (Sat + Sun)."""
        total = sum(p.total_amount for p in self.day_patterns)
        if total == 0:
            return 0.0
        weekend = sum(
            p.total_amount for p in self.day_patterns
            if p.day in (DayOfWeek.SATURDAY, DayOfWeek.SUNDAY)
        )
        return (weekend / total) * 100


@dataclass(frozen=True)
class Anomaly:
    """A detected spending anomaly.

    Attributes:
        transaction_date: Date of the transaction.
        description: Transaction description.
        amount: Transaction amount.
        category: Transaction category.
        z_score: Standard deviations from mean.
        anomaly_type: Type of anomaly (high, low, unusual).
        reason: Explanation of why it's anomalous.
    """

    transaction_date: str
    description: str
    amount: float
    category: str
    z_score: float
    anomaly_type: str
    reason: str


@dataclass
class AnomalyReport:
    """Report of detected anomalies.

    Attributes:
        anomalies: List of detected anomalies.
        total_transactions: Total transactions analyzed.
        anomaly_rate: Percentage of transactions flagged.
    """

    anomalies: list[Anomaly] = field(default_factory=list)
    total_transactions: int = 0

    @property
    def anomaly_rate(self) -> float:
        """Percentage of transactions that are anomalies."""
        if self.total_transactions == 0:
            return 0.0
        return (len(self.anomalies) / self.total_transactions) * 100

    def high_amount_anomalies(self) -> list[Anomaly]:
        """Get anomalies due to unusually high amounts."""
        return [a for a in self.anomalies if a.anomaly_type == "high"]


@dataclass(frozen=True)
class SavingsRateTrend:
    """Savings rate for a specific period.

    Attributes:
        period: Time period (e.g., "2024-01").
        earnings: Total earnings.
        expenses: Total expenses.
        savings: Net savings (earnings - expenses).
        savings_rate: Savings as percentage of earnings.
    """

    period: str
    earnings: float
    expenses: float
    savings: float
    savings_rate: float


class SpendingPatternService:
    """Service for analyzing spending patterns."""

    def __init__(
        self,
        *,
        anomaly_threshold: float = 2.0,
    ) -> None:
        """Initialize the spending pattern service.

        Args:
            anomaly_threshold: Z-score threshold for anomaly detection.
        """
        self._anomaly_threshold = anomaly_threshold

    def pareto_analysis(
        self,
        *,
        transactions: pd.DataFrame,
        group_by: str = "category",
    ) -> ParetoAnalysis:
        """Perform Pareto (80/20) analysis on spending.

        Args:
            transactions: DataFrame with transaction data.
            group_by: Column to group by (category, sub_category, etc.).

        Returns:
            ParetoAnalysis showing spending distribution.
        """
        if transactions.empty or group_by not in transactions.columns:
            return ParetoAnalysis()

        # Filter to expenses and get absolute amounts
        df = transactions.copy()
        if "amount" in df.columns:
            df = df[df["amount"] < 0].copy()
            df["abs_amount"] = df["amount"].abs()
        else:
            return ParetoAnalysis()

        # Group and sum
        grouped = df.groupby(group_by)["abs_amount"].sum().sort_values(ascending=False)
        total = grouped.sum()

        if total == 0:
            return ParetoAnalysis()

        # Build Pareto items
        items = []
        cumulative = 0.0

        for category, amount in grouped.items():
            percentage = (amount / total) * 100
            cumulative += percentage
            is_top_80 = cumulative <= 80 or (cumulative > 80 and cumulative - percentage < 80)

            items.append(ParetoItem(
                category=str(category),
                amount=float(amount),
                percentage=percentage,
                cumulative_percentage=cumulative,
                is_top_80=is_top_80,
            ))

        return ParetoAnalysis(items=items, total_amount=float(total))

    def weekly_pattern(
        self,
        *,
        transactions: pd.DataFrame,
    ) -> WeeklyPattern:
        """Analyze spending by day of week.

        Args:
            transactions: DataFrame with transaction data.

        Returns:
            WeeklyPattern showing daily spending distribution.
        """
        if transactions.empty:
            return WeeklyPattern()

        df = transactions.copy()

        # Ensure we have date and amount columns
        if "transaction_date" not in df.columns or "amount" not in df.columns:
            return WeeklyPattern()

        # Filter to expenses
        df = df[df["amount"] < 0].copy()
        df["abs_amount"] = df["amount"].abs()

        # Parse dates and get day of week
        df["date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df["day_of_week"] = df["date"].dt.dayofweek

        # Calculate weekly total for percentages
        weekly_total = df["abs_amount"].sum()

        # Group by day
        day_patterns = []
        for day_num in range(7):
            day_data = df[df["day_of_week"] == day_num]
            total_amount = float(day_data["abs_amount"].sum()) if not day_data.empty else 0.0
            count = len(day_data)
            avg = total_amount / count if count > 0 else 0.0
            pct = (total_amount / weekly_total * 100) if weekly_total > 0 else 0.0

            day_patterns.append(DayPattern(
                day=DayOfWeek.from_int(day_num),
                total_amount=total_amount,
                transaction_count=count,
                average_transaction=avg,
                percentage_of_week=pct,
            ))

        return WeeklyPattern(day_patterns=day_patterns)

    def detect_anomalies(
        self,
        *,
        transactions: pd.DataFrame,
        by_category: bool = True,
    ) -> AnomalyReport:
        """Detect anomalous transactions.

        Uses Z-score to identify transactions that deviate significantly
        from the mean spending pattern.

        Args:
            transactions: DataFrame with transaction data.
            by_category: If True, calculate anomalies within each category.

        Returns:
            AnomalyReport with detected anomalies.
        """
        if transactions.empty or "amount" not in transactions.columns:
            return AnomalyReport()

        df = transactions.copy()
        df = df[df["amount"] < 0].copy()  # Expenses only
        df["abs_amount"] = df["amount"].abs()

        if df.empty:
            return AnomalyReport()

        anomalies = []
        total = len(df)

        if by_category and "category" in df.columns:
            # Detect anomalies within each category
            for category in df["category"].unique():
                cat_df = df[df["category"] == category]
                cat_anomalies = self._find_anomalies_in_group(cat_df, category)
                anomalies.extend(cat_anomalies)
        else:
            # Detect anomalies across all transactions
            anomalies = self._find_anomalies_in_group(df, "all")

        return AnomalyReport(anomalies=anomalies, total_transactions=total)

    def _find_anomalies_in_group(
        self,
        df: pd.DataFrame,
        category: str,
    ) -> list[Anomaly]:
        """Find anomalies within a group of transactions."""
        if len(df) < 3:  # Need enough data for meaningful statistics
            return []

        mean = df["abs_amount"].mean()
        std = df["abs_amount"].std()

        if std == 0:  # No variation
            return []

        anomalies = []

        for _, row in df.iterrows():
            amount = row["abs_amount"]
            z_score = (amount - mean) / std

            if abs(z_score) >= self._anomaly_threshold:
                anomaly_type = "high" if z_score > 0 else "low"
                reason = (
                    f"Amount ${amount:.2f} is {abs(z_score):.1f} standard deviations "
                    f"{'above' if z_score > 0 else 'below'} average ${mean:.2f}"
                )

                anomalies.append(Anomaly(
                    transaction_date=str(row.get("transaction_date", "")),
                    description=str(row.get("description", "")),
                    amount=float(amount),
                    category=str(row.get("category", category)),
                    z_score=float(z_score),
                    anomaly_type=anomaly_type,
                    reason=reason,
                ))

        return anomalies

    def savings_rate_trend(
        self,
        *,
        earnings: pd.DataFrame,
        expenses: pd.DataFrame,
    ) -> list[SavingsRateTrend]:
        """Calculate savings rate over time.

        Args:
            earnings: DataFrame with earnings transactions.
            expenses: DataFrame with expense transactions.

        Returns:
            List of SavingsRateTrend for each period.
        """
        # Prepare earnings by month
        earnings_by_month = self._aggregate_by_month(earnings, is_expense=False)
        expenses_by_month = self._aggregate_by_month(expenses, is_expense=True)

        # Get all periods
        all_periods = set(earnings_by_month.keys()) | set(expenses_by_month.keys())

        trends = []
        for period in sorted(all_periods):
            earn = earnings_by_month.get(period, 0.0)
            exp = expenses_by_month.get(period, 0.0)
            savings = earn - exp
            rate = (savings / earn * 100) if earn > 0 else 0.0

            trends.append(SavingsRateTrend(
                period=period,
                earnings=earn,
                expenses=exp,
                savings=savings,
                savings_rate=rate,
            ))

        return trends

    def _aggregate_by_month(
        self,
        df: pd.DataFrame,
        *,
        is_expense: bool,
    ) -> dict[str, float]:
        """Aggregate amounts by month."""
        if df.empty or "amount" not in df.columns:
            return {}

        df = df.copy()

        # Parse dates
        if "transaction_date" in df.columns:
            df["date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
            df["period"] = df["date"].dt.strftime("%Y-%m")
        elif "year_month" in df.columns:
            df["period"] = df["year_month"].astype(str)
        else:
            return {}

        df = df.dropna(subset=["period"])

        # Aggregate
        if is_expense:
            # Make expenses positive for summing
            df["abs_amount"] = df["amount"].abs()
            return df.groupby("period")["abs_amount"].sum().to_dict()
        else:
            return df.groupby("period")["amount"].sum().to_dict()


def analyze_spending_patterns(
    *,
    transactions: pd.DataFrame,
) -> dict:
    """Convenience function for comprehensive spending analysis.

    Args:
        transactions: DataFrame with transaction data.

    Returns:
        Dictionary containing pareto, weekly, and anomaly analyses.
    """
    service = SpendingPatternService()

    return {
        "pareto": service.pareto_analysis(transactions=transactions),
        "weekly": service.weekly_pattern(transactions=transactions),
        "anomalies": service.detect_anomalies(transactions=transactions),
    }
