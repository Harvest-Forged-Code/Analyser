"""Spending pattern analysis service (business logic).

Provides:
- Pareto analysis (80/20 rule for categories)
- Day-of-week spending patterns
- Anomaly detection (outlier transactions)
- Savings rate trends
"""

from __future__ import annotations

import pandas as pd

from budget_analyser.features.trends.models import (
    Anomaly,
    AnomalyReport,
    DayOfWeek,
    DayPattern,
    ParetoAnalysis,
    ParetoItem,
    SavingsRateTrend,
    WeeklyPattern,
)


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
            group_by: Column to group by.

        Returns:
            ParetoAnalysis showing spending distribution.

        Example:
            >>> import pandas as pd
            >>> service = SpendingPatternService()
            >>> df = pd.DataFrame({
            ...     "amount": [-500, -200, -100],
            ...     "category": ["Food", "Transport", "Other"],
            ... })
            >>> result = service.pareto_analysis(
            ...     transactions=df,
            ... )
            >>> result.total_amount
            800.0
        """
        if (transactions.empty
                or group_by not in transactions.columns):
            return ParetoAnalysis()

        df = transactions.copy()
        if "amount" in df.columns:
            df = df[df["amount"] < 0].copy()
            df["abs_amount"] = df["amount"].abs()
        else:
            return ParetoAnalysis()

        grouped = (
            df.groupby(group_by)["abs_amount"]
            .sum()
            .sort_values(ascending=False)
        )
        total = grouped.sum()

        if total == 0:
            return ParetoAnalysis()

        items = []
        cumulative = 0.0

        for category, amount in grouped.items():
            percentage = (amount / total) * 100
            cumulative += percentage
            is_top_80 = (
                cumulative <= 80
                or cumulative - percentage < 80
            )

            items.append(ParetoItem(
                category=str(category),
                amount=float(amount),
                percentage=percentage,
                cumulative_percentage=cumulative,
                is_top_80=is_top_80,
            ))

        return ParetoAnalysis(
            items=items, total_amount=float(total),
        )

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

        Example:
            >>> import pandas as pd
            >>> service = SpendingPatternService()
            >>> df = pd.DataFrame({
            ...     "amount": [-50, -30, -20],
            ...     "transaction_date": [
            ...         "2024-01-15", "2024-01-16", "2024-01-17",
            ...     ],
            ... })
            >>> result = service.weekly_pattern(
            ...     transactions=df,
            ... )
            >>> len(result.day_patterns)
            7
        """
        if transactions.empty:
            return WeeklyPattern()

        df = transactions.copy()

        if ("transaction_date" not in df.columns
                or "amount" not in df.columns):
            return WeeklyPattern()

        df = df[df["amount"] < 0].copy()
        df["abs_amount"] = df["amount"].abs()

        df["date"] = pd.to_datetime(
            df["transaction_date"], errors="coerce",
        )
        df = df.dropna(subset=["date"])
        df["day_of_week"] = df["date"].dt.dayofweek

        weekly_total = df["abs_amount"].sum()

        day_patterns = []
        for day_num in range(7):
            day_data = df[df["day_of_week"] == day_num]
            total_amount = (
                float(day_data["abs_amount"].sum())
                if not day_data.empty else 0.0
            )
            count = len(day_data)
            avg = total_amount / count if count > 0 else 0.0
            pct = (
                (total_amount / weekly_total * 100)
                if weekly_total > 0 else 0.0
            )

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

        Args:
            transactions: DataFrame with transaction data.
            by_category: If True, detect within each category.

        Returns:
            AnomalyReport with detected anomalies.

        Example:
            >>> import pandas as pd
            >>> service = SpendingPatternService()
            >>> df = pd.DataFrame({
            ...     "amount": [-10, -15, -12, -500],
            ...     "category": ["Food"] * 4,
            ...     "description": ["a", "b", "c", "d"],
            ...     "transaction_date": [
            ...         "2024-01-01", "2024-01-02",
            ...         "2024-01-03", "2024-01-04",
            ...     ],
            ... })
            >>> report = service.detect_anomalies(
            ...     transactions=df,
            ... )
            >>> report.total_transactions > 0
            True
        """
        if (transactions.empty
                or "amount" not in transactions.columns):
            return AnomalyReport()

        df = transactions.copy()
        df = df[df["amount"] < 0].copy()
        df["abs_amount"] = df["amount"].abs()

        if df.empty:
            return AnomalyReport()

        anomalies = []
        total = len(df)

        if by_category and "category" in df.columns:
            for category in df["category"].unique():
                cat_df = df[df["category"] == category]
                cat_anomalies = self._find_anomalies_in_group(
                    cat_df, category,
                )
                anomalies.extend(cat_anomalies)
        else:
            anomalies = self._find_anomalies_in_group(df, "all")

        return AnomalyReport(
            anomalies=anomalies, total_transactions=total,
        )

    def _find_anomalies_in_group(
        self,
        df: pd.DataFrame,
        category: str,
    ) -> list[Anomaly]:
        """Find anomalies within a group of transactions.

        Uses z-score analysis to identify transactions whose
        absolute amount deviates from the group mean by more
        than the configured anomaly_threshold.

        Args:
            df: DataFrame of transactions for a single group,
                must contain an 'abs_amount' column.
            category: Category label for the group.

        Returns:
            List of Anomaly objects for transactions exceeding
            the z-score threshold. Empty if fewer than 3
            transactions or zero standard deviation.
        """
        if len(df) < 3:
            return []

        mean = df["abs_amount"].mean()
        std = df["abs_amount"].std()

        if std == 0:
            return []

        anomalies = []

        for _, row in df.iterrows():
            amount = row["abs_amount"]
            z_score = (amount - mean) / std

            if abs(z_score) >= self._anomaly_threshold:
                anomaly_type = "high" if z_score > 0 else "low"
                direction = (
                    "above" if z_score > 0 else "below"
                )
                reason = (
                    f"Amount ${amount:.2f} is "
                    f"{abs(z_score):.1f} standard deviations "
                    f"{direction} average ${mean:.2f}"
                )

                anomalies.append(Anomaly(
                    transaction_date=str(
                        row.get("transaction_date", ""),
                    ),
                    description=str(
                        row.get("description", ""),
                    ),
                    amount=float(amount),
                    category=str(
                        row.get("category", category),
                    ),
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

        Example:
            >>> import pandas as pd
            >>> service = SpendingPatternService()
            >>> earn = pd.DataFrame({
            ...     "amount": [3000, 3100],
            ...     "transaction_date": [
            ...         "2024-01-01", "2024-02-01",
            ...     ],
            ... })
            >>> exp = pd.DataFrame({
            ...     "amount": [-2000, -2100],
            ...     "transaction_date": [
            ...         "2024-01-15", "2024-02-15",
            ...     ],
            ... })
            >>> trends = service.savings_rate_trend(
            ...     earnings=earn, expenses=exp,
            ... )
            >>> len(trends)
            2
        """
        earnings_by_month = self._aggregate_by_month(
            earnings, is_expense=False,
        )
        expenses_by_month = self._aggregate_by_month(
            expenses, is_expense=True,
        )

        all_periods = (
            set(earnings_by_month.keys())
            | set(expenses_by_month.keys())
        )

        trends = []
        for period in sorted(all_periods):
            earn = earnings_by_month.get(period, 0.0)
            exp = expenses_by_month.get(period, 0.0)
            savings = earn - exp
            rate = (
                (savings / earn * 100) if earn > 0 else 0.0
            )

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
        """Aggregate amounts by month.

        Groups transactions by month and sums amounts. For expenses,
        uses absolute values; for earnings, uses raw values.

        Args:
            df: DataFrame with 'amount' and either
                'transaction_date' or 'year_month' column.
            is_expense: If True, take absolute values of amounts.

        Returns:
            Dict mapping period string ("YYYY-MM") to total amount.
        """
        if df.empty or "amount" not in df.columns:
            return {}

        df = df.copy()

        if "transaction_date" in df.columns:
            df["date"] = pd.to_datetime(
                df["transaction_date"], errors="coerce",
            )
            df["period"] = df["date"].dt.strftime("%Y-%m")
        elif "year_month" in df.columns:
            df["period"] = df["year_month"].astype(str)
        else:
            return {}

        df = df.dropna(subset=["period"])

        if is_expense:
            df["abs_amount"] = df["amount"].abs()
            return (
                df.groupby("period")["abs_amount"]
                .sum()
                .to_dict()
            )

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

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "amount": [-100, -200, -50],
        ...     "category": ["Food", "Transport", "Other"],
        ...     "transaction_date": [
        ...         "2024-01-15", "2024-01-16", "2024-01-17",
        ...     ],
        ... })
        >>> results = analyze_spending_patterns(transactions=df)
        >>> set(results.keys())
        {'pareto', 'weekly', 'anomalies'}
    """
    service = SpendingPatternService()

    return {
        "pareto": service.pareto_analysis(
            transactions=transactions,
        ),
        "weekly": service.weekly_pattern(
            transactions=transactions,
        ),
        "anomalies": service.detect_anomalies(
            transactions=transactions,
        ),
    }
