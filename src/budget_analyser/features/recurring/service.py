"""Recurring payment analytics service.

Business logic for recurring transaction detection, anomaly analysis,
and summary generation. Reads from the main transactions database and
persists recurring data through ``RecurringModel``.
"""

from __future__ import annotations

import logging
import math
import re
import sqlite3
import statistics
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from budget_analyser.features.recurring.models import (
    RecurringAnomaly,
    RecurringDetection,
    RecurringModel,
    RecurringSummary,
    RecurringTransaction,
)

# ---------------------------------------------------------------------------
# Frequency-to-monthly multipliers
# ---------------------------------------------------------------------------

_FREQUENCY_TO_MONTHLY: dict[str, float] = {
    "daily": 30.0,
    "weekly": 4.33,
    "bi-weekly": 2.17,
    "monthly": 1.0,
    "quarterly": 1.0 / 3.0,
    "semi-annual": 1.0 / 6.0,
    "yearly": 1.0 / 12.0,
}

# ---------------------------------------------------------------------------
# Expected interval in days per frequency (for anomaly detection)
# ---------------------------------------------------------------------------

_FREQUENCY_TO_DAYS: dict[str, float] = {
    "daily": 1.0,
    "weekly": 7.0,
    "bi-weekly": 14.0,
    "monthly": 30.0,
    "quarterly": 90.0,
    "semi-annual": 182.0,
    "yearly": 365.0,
}

# ---------------------------------------------------------------------------
# Pure helper functions
# ---------------------------------------------------------------------------

# Patterns stripped from the end of descriptions
_DATE_PATTERN = re.compile(
    r"\s*\d{1,2}/\d{1,2}(?:/\d{2,4})?\s*$"
)
_REF_PATTERN = re.compile(
    r"\s*(?:#[A-Za-z0-9]+|REF:[A-Za-z0-9]+)\s*$", re.IGNORECASE
)
_TRAILING_ID_PATTERN = re.compile(r"\s+\d{5,}\s*$")
_MULTI_WHITESPACE = re.compile(r"\s+")


def normalize_description(text: str) -> str:
    """Normalize a transaction description for matching.

    Applies the following transformations in order:

    - Lowercase the text
    - Strip trailing date patterns (MM/DD, MM/DD/YY, MM/DD/YYYY)
    - Strip trailing reference numbers (#123456, REF:ABC)
    - Strip trailing transaction IDs (digit sequences > 4 chars)
    - Collapse multiple whitespace to a single space
    - Strip leading/trailing whitespace

    Args:
        text: Raw transaction description.

    Returns:
        Cleaned, normalized description string.
    """
    result = text.lower()
    result = _DATE_PATTERN.sub("", result)
    result = _REF_PATTERN.sub("", result)
    result = _TRAILING_ID_PATTERN.sub("", result)
    result = _MULTI_WHITESPACE.sub(" ", result)
    return result.strip()


def estimate_frequency(median_interval: float) -> str | None:
    """Estimate payment frequency from median interval in days.

    Maps the median interval between transactions to a named
    frequency bucket. Returns ``None`` when the interval does
    not match any known bucket.

    Args:
        median_interval: Median number of days between occurrences.

    Returns:
        Frequency name or None if no bucket matches.
    """
    buckets: list[tuple[float, float, str]] = [
        (0, 2, "daily"),
        (5, 9, "weekly"),
        (12, 16, "bi-weekly"),
        (25, 35, "monthly"),
        (80, 100, "quarterly"),
        (165, 200, "semi-annual"),
        (350, 380, "yearly"),
    ]
    for low, high, name in buckets:
        if low <= median_interval <= high:
            return name
    return None


def calculate_confidence(
    *,
    occurrences: int,
    interval_std: float,
    median_interval: float,
    amount_cv: float,
    days_since_last: float,
    expected_interval: float,
) -> float:
    """Calculate confidence score for a recurring detection.

    Uses a weighted combination of four signals:

    - **Occurrence count (30 %):** ``min(log2(count) / log2(12), 1.0)``
    - **Interval consistency (30 %):** ``max(1 - std / median, 0)``
    - **Amount consistency (25 %):** ``max(1 - amount_cv, 0)``
    - **Recency (15 %):** 1.0 if recent, exponential decay otherwise

    Args:
        occurrences: Number of observed transactions.
        interval_std: Standard deviation of intervals in days.
        median_interval: Median interval in days.
        amount_cv: Coefficient of variation of transaction amounts.
        days_since_last: Days since the most recent transaction.
        expected_interval: Expected interval for the detected frequency.

    Returns:
        Confidence score clamped to the range 0.0 -- 1.0.
    """
    # Occurrence score
    if occurrences <= 1:
        occ_score = 0.0
    else:
        occ_score = min(math.log2(occurrences) / math.log2(12), 1.0)

    # Interval consistency score
    if median_interval > 0:
        interval_score = max(1.0 - (interval_std / median_interval), 0.0)
    else:
        interval_score = 0.0

    # Amount consistency score
    amount_score = max(1.0 - amount_cv, 0.0)

    # Recency score
    threshold = expected_interval * 1.5
    if days_since_last <= threshold:
        recency_score = 1.0
    else:
        overshoot = days_since_last - threshold
        recency_score = math.exp(-overshoot / expected_interval)

    score = (
        0.30 * occ_score
        + 0.30 * interval_score
        + 0.25 * amount_score
        + 0.15 * recency_score
    )
    return max(0.0, min(1.0, score))


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class RecurringAnalyticsService:
    """Service for recurring payment detection, management, and anomaly detection.

    Orchestrates auto-detection of recurring patterns from the main
    transaction history, provides CRUD operations for confirmed and
    manual entries, and detects anomalies such as missed payments or
    unexpected amount changes.

    Example:
        >>> from pathlib import Path
        >>> model = RecurringModel(db_path=Path("budget.db"))
        >>> svc = RecurringAnalyticsService(
        ...     model=model, db_path=Path("transactions.db"),
        ... )
        >>> detections = svc.detect_recurring_transactions()
    """

    def __init__(
        self,
        *,
        model: RecurringModel,
        db_path: Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the recurring analytics service.

        Args:
            model: RecurringModel for persistence of recurring data.
            db_path: Path to the main transactions database (read-only).
            logger: Optional logger for diagnostics.
        """
        self._model = model
        self._db_path = db_path
        self._logger = logger or logging.getLogger(
            "budget_analyser.features.recurring.service"
        )

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def _load_transactions(self) -> pd.DataFrame:
        """Load transactions from the main database.

        Returns:
            DataFrame with transaction_date, description, amount,
            category, and sub_category columns.
        """
        conn = sqlite3.connect(str(self._db_path))
        try:
            df = pd.read_sql_query(
                "SELECT transaction_date, description, amount, "
                "category, sub_category FROM transactions",
                conn,
            )
        finally:
            conn.close()
        return df

    def _existing_descriptions(self) -> set[str]:
        """Get normalized descriptions already tracked as recurring.

        Returns:
            Set of lowercase description strings.
        """
        existing = self._model.get_all_recurring()
        return {
            normalize_description(r.description) for r in existing
        }

    def detect_recurring_transactions(
        self,
        *,
        threshold: float = 0.5,
    ) -> list[RecurringDetection]:
        """Detect recurring patterns in transaction history.

        Scans the main transactions database, groups transactions by
        normalized description and rounded amount, then evaluates each
        group for recurring patterns using interval analysis and
        confidence scoring.

        Args:
            threshold: Minimum confidence score to include a detection
                in the results. Defaults to 0.5.

        Returns:
            List of RecurringDetection results sorted by confidence
            descending.
        """
        df = self._load_transactions()
        if df.empty:
            return []

        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"], errors="coerce"
        )
        df = df.dropna(subset=["transaction_date"])
        if df.empty:
            return []

        df["norm_desc"] = df["description"].apply(normalize_description)
        df["rounded_amount"] = df["amount"].round(0)

        existing = self._existing_descriptions()
        detections: list[RecurringDetection] = []

        grouped = df.groupby(["norm_desc", "rounded_amount"])
        for (norm_desc, _rounded), group in grouped:
            if len(group) < 2 or norm_desc in existing:
                continue
            detection = self._evaluate_group(
                group=group, threshold=threshold,
            )
            if detection is not None:
                detections.append(detection)

        detections.sort(key=lambda d: d.confidence_score, reverse=True)
        self._logger.info(
            "Detected %d recurring patterns (threshold=%.2f)",
            len(detections), threshold,
        )
        return detections

    @staticmethod
    def _compute_group_stats(
        *,
        dates: list[date],
        amounts: list[float],
    ) -> tuple[str, float, float, float] | None:
        """Compute interval and amount statistics for a group.

        Args:
            dates: Sorted list of transaction dates.
            amounts: Corresponding transaction amounts.

        Returns:
            Tuple of (frequency, med_interval, amount_std, amount_cv)
            or None if no valid frequency is detected.
        """
        intervals = [
            (dates[i] - dates[i - 1]).days
            for i in range(1, len(dates))
        ]
        if not intervals:
            return None

        med_interval = statistics.median(intervals)
        frequency = estimate_frequency(med_interval)
        if frequency is None:
            return None

        interval_std = (
            statistics.stdev(intervals) if len(intervals) > 1
            else 0.0
        )
        mean_amount = statistics.mean(amounts)
        amount_std = (
            statistics.stdev(amounts) if len(amounts) > 1
            else 0.0
        )
        amount_cv = (
            abs(amount_std / mean_amount) if mean_amount != 0
            else 0.0
        )

        expected_interval = _FREQUENCY_TO_DAYS.get(
            frequency, med_interval,
        )
        days_since = (date.today() - dates[-1]).days

        confidence = calculate_confidence(
            occurrences=len(dates),
            interval_std=interval_std,
            median_interval=med_interval,
            amount_cv=amount_cv,
            days_since_last=float(days_since),
            expected_interval=expected_interval,
        )
        return frequency, confidence, amount_std, mean_amount

    def _evaluate_group(
        self,
        *,
        group: pd.DataFrame,
        threshold: float,
    ) -> RecurringDetection | None:
        """Evaluate a transaction group for recurring patterns.

        Analyses dates and amounts in the group to determine whether
        transactions recur at a recognisable frequency above the
        confidence threshold.

        Args:
            group: DataFrame subset sharing the same normalized
                description and rounded amount.
            threshold: Minimum confidence score.

        Returns:
            A RecurringDetection if the group qualifies, else None.
        """
        sorted_group = group.sort_values("transaction_date")
        dates = sorted_group["transaction_date"].dt.date.tolist()
        amounts = sorted_group["amount"].tolist()

        result = self._compute_group_stats(
            dates=dates, amounts=amounts,
        )
        if result is None:
            return None

        frequency, confidence, amount_std, mean_amount = result
        if confidence < threshold:
            return None

        last_row = sorted_group.iloc[-1]
        return RecurringDetection(
            description=str(last_row["description"]),
            expected_amount=round(mean_amount, 2),
            amount_variance=round(amount_std, 2),
            frequency=frequency,
            category=str(last_row.get("category", "")),
            sub_category=str(last_row.get("sub_category", "")),
            last_occurrence=dates[-1].isoformat(),
            occurrences=len(dates),
            confidence_score=round(confidence, 4),
            matching_dates=[d.isoformat() for d in dates],
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def confirm_detection(
        self,
        recurring_id: int,
    ) -> RecurringTransaction | None:
        """Confirm a detected recurring transaction.

        Args:
            recurring_id: The primary key of the recurring record.

        Returns:
            The updated RecurringTransaction, or None if not found.
        """
        return self._model.confirm_recurring(recurring_id)

    def dismiss_detection(
        self,
        recurring_id: int,
    ) -> RecurringTransaction | None:
        """Dismiss a detected recurring transaction.

        Marks the entry as inactive so it no longer appears in the
        active list.

        Args:
            recurring_id: The primary key of the recurring record.

        Returns:
            The updated RecurringTransaction, or None if not found.
        """
        return self._model.dismiss_recurring(recurring_id)

    def mark_expected(
        self,
        recurring_id: int,
        *,
        is_expected: bool,
    ) -> RecurringTransaction | None:
        """Set whether a payment is currently expected.

        Args:
            recurring_id: The primary key of the recurring record.
            is_expected: Whether the next payment is expected.

        Returns:
            The updated RecurringTransaction, or None if not found.
        """
        return self._model.update_recurring(
            recurring_id, is_expected=is_expected,
        )

    def add_manual_recurring(
        self,
        *,
        description: str,
        expected_amount: float,
        frequency: str = "monthly",
        category: str = "",
        sub_category: str = "",
    ) -> RecurringTransaction:
        """Add a manually created recurring transaction.

        The entry is automatically marked as user-confirmed with
        full confidence and set as expected.

        Args:
            description: Transaction description text.
            expected_amount: Expected payment amount.
            frequency: Payment frequency. Defaults to "monthly".
            category: Top-level expense category.
            sub_category: Detailed sub-category label.

        Returns:
            The saved RecurringTransaction.
        """
        return self._model.save_recurring(
            description=description,
            expected_amount=expected_amount,
            amount_variance=0.0,
            frequency=frequency,
            category=category,
            sub_category=sub_category,
            last_occurrence=None,
            next_expected=None,
            confidence_score=1.0,
            user_confirmed=True,
            is_expected=True,
            is_active=True,
            detection_method="manual",
        )

    def update_recurring(
        self,
        recurring_id: int,
        **kwargs: object,
    ) -> RecurringTransaction | None:
        """Partially update a recurring transaction.

        Delegates to the model layer. Only updatable fields are
        accepted (description, expected_amount, amount_variance,
        frequency, category, sub_category, is_expected,
        last_occurrence, next_expected).

        Args:
            recurring_id: The primary key of the recurring record.
            **kwargs: Field names and their new values.

        Returns:
            The updated RecurringTransaction, or None if not found.

        Raises:
            ValueError: If an unsupported field name is provided.
        """
        return self._model.update_recurring(recurring_id, **kwargs)

    def delete_recurring(self, recurring_id: int) -> bool:
        """Delete a recurring transaction and its anomalies.

        Args:
            recurring_id: The primary key of the recurring record.

        Returns:
            True if the record was deleted, False if not found.
        """
        return self._model.delete_recurring(recurring_id)

    def get_all_recurring(
        self,
        *,
        active_only: bool = False,
    ) -> list[RecurringTransaction]:
        """Get all recurring transactions.

        Args:
            active_only: If True, return only active entries.

        Returns:
            List of RecurringTransaction entries.
        """
        return self._model.get_all_recurring(active_only=active_only)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_active_count(self) -> int:
        """Count of active recurring transactions.

        Returns:
            Number of active recurring entries.
        """
        active = self._model.get_all_recurring(active_only=True)
        return len(active)

    def get_monthly_recurring_cost(self) -> float:
        """Total monthly cost normalized across all frequencies.

        Each recurring transaction's expected amount is multiplied by
        its frequency-to-monthly conversion factor (e.g. weekly * 4.33,
        quarterly / 3).

        Returns:
            Total estimated monthly cost in dollars.
        """
        active = self._model.get_all_recurring(active_only=True)
        total = 0.0
        for txn in active:
            multiplier = _FREQUENCY_TO_MONTHLY.get(txn.frequency, 1.0)
            total += abs(txn.expected_amount) * multiplier
        return round(total, 2)

    def get_summary(self) -> RecurringSummary:
        """Generate a full analytics summary of recurring transactions.

        Aggregates active recurring entries into counts, costs by
        frequency and category, and projects annual totals.

        Returns:
            RecurringSummary with all computed metrics.
        """
        all_recurring = self._model.get_all_recurring()
        active = [r for r in all_recurring if r.is_active]

        confirmed = sum(1 for r in active if r.user_confirmed)
        unconfirmed = len(active) - confirmed

        by_frequency: dict[str, int] = {}
        by_category: dict[str, float] = {}

        for txn in active:
            by_frequency[txn.frequency] = (
                by_frequency.get(txn.frequency, 0) + 1
            )
            multiplier = _FREQUENCY_TO_MONTHLY.get(
                txn.frequency, 1.0,
            )
            monthly_cost = abs(txn.expected_amount) * multiplier
            cat = txn.category or "Uncategorized"
            by_category[cat] = round(
                by_category.get(cat, 0.0) + monthly_cost, 2,
            )

        monthly_cost_total = self.get_monthly_recurring_cost()

        return RecurringSummary(
            total_monthly_cost=monthly_cost_total,
            total_yearly_projection=round(monthly_cost_total * 12, 2),
            active_count=len(active),
            confirmed_count=confirmed,
            unconfirmed_count=unconfirmed,
            by_frequency=by_frequency,
            by_category=by_category,
            trend_data=[],
        )

    # ------------------------------------------------------------------
    # Anomaly detection
    # ------------------------------------------------------------------

    def _query_transactions_for_description(
        self,
        description: str,
    ) -> list[tuple[str, float]]:
        """Query matching transactions from the main database.

        Uses a LIKE match against the normalized description to find
        all transactions that correspond to a recurring entry.

        Args:
            description: The recurring transaction description.

        Returns:
            List of (transaction_date, amount) tuples sorted by date.
        """
        norm = normalize_description(description)
        conn = sqlite3.connect(str(self._db_path))
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT transaction_date, amount FROM transactions "
                "WHERE LOWER(description) LIKE ? "
                "ORDER BY transaction_date",
                (f"%{norm}%",),
            )
            rows = cursor.fetchall()
        finally:
            conn.close()
        return [
            (row["transaction_date"], row["amount"]) for row in rows
        ]

    def _check_missed_payment(  # pylint: disable=too-many-arguments
        self,
        *,
        recurring: RecurringTransaction,
        last_date: date,
        days_since: int,
        expected_days: float,
    ) -> RecurringAnomaly | None:
        """Check for a missed payment anomaly.

        Args:
            recurring: The recurring transaction entry.
            last_date: Date of the most recent matching transaction.
            days_since: Days elapsed since last_date.
            expected_days: Expected interval in days.

        Returns:
            A saved RecurringAnomaly if overdue, else None.
        """
        if days_since <= expected_days * 1.5:
            return None

        severity = (
            "critical" if days_since >= expected_days * 2
            else "warning"
        )
        expected_next = last_date + timedelta(
            days=int(expected_days),
        )
        return self._model.save_anomaly(
            recurring_id=recurring.id,
            anomaly_type="missed_payment",
            expected_date=expected_next.isoformat(),
            actual_date=None,
            expected_amount=recurring.expected_amount,
            actual_amount=None,
            severity=severity,
            message=(
                f"Expected {recurring.frequency} payment for "
                f"'{recurring.description}' is "
                f"{days_since} days overdue"
            ),
        )

    def _check_amount_spike(
        self,
        *,
        recurring: RecurringTransaction,
        last_date_str: str,
        last_amount: float,
    ) -> RecurringAnomaly | None:
        """Check for an amount spike anomaly.

        Args:
            recurring: The recurring transaction entry.
            last_date_str: ISO date string of the last transaction.
            last_amount: Amount of the last transaction.

        Returns:
            A saved RecurringAnomaly if spiked, else None.
        """
        variance = recurring.amount_variance
        if variance <= 0:
            return None

        spike_threshold = (
            abs(recurring.expected_amount) + 2 * variance
        )
        if abs(last_amount) <= spike_threshold:
            return None

        diff = abs(last_amount) - abs(recurring.expected_amount)
        severity = (
            "critical" if diff >= 3 * variance else "warning"
        )
        return self._model.save_anomaly(
            recurring_id=recurring.id,
            anomaly_type="amount_spike",
            expected_date=None,
            actual_date=last_date_str,
            expected_amount=recurring.expected_amount,
            actual_amount=last_amount,
            severity=severity,
            message=(
                f"Amount ${abs(last_amount):.2f} for "
                f"'{recurring.description}' exceeds "
                f"expected ${abs(recurring.expected_amount):.2f}"
                f" by ${diff:.2f}"
            ),
        )

    def detect_anomalies(self) -> list[RecurringAnomaly]:
        """Detect anomalies for all active recurring transactions.

        Checks each active recurring entry for:

        - **Missed payments:** The last matching transaction is more
          than 1.5x the expected interval ago.
        - **Amount spikes:** The most recent transaction amount
          exceeds the expected amount plus twice the variance.

        New anomalies are saved to the database.

        Returns:
            List of newly detected RecurringAnomaly entries.
        """
        active = self._model.get_all_recurring(active_only=True)
        new_anomalies: list[RecurringAnomaly] = []
        today = date.today()

        for recurring in active:
            expected_days = _FREQUENCY_TO_DAYS.get(
                recurring.frequency, 30.0,
            )
            matches = self._query_transactions_for_description(
                recurring.description,
            )
            if not matches:
                continue

            last_date_str, last_amount = matches[-1]
            try:
                last_date = date.fromisoformat(last_date_str)
            except (ValueError, TypeError):
                continue

            days_since = (today - last_date).days

            missed = self._check_missed_payment(
                recurring=recurring,
                last_date=last_date,
                days_since=days_since,
                expected_days=expected_days,
            )
            if missed is not None:
                new_anomalies.append(missed)

            spike = self._check_amount_spike(
                recurring=recurring,
                last_date_str=last_date_str,
                last_amount=last_amount,
            )
            if spike is not None:
                new_anomalies.append(spike)

        self._logger.info(
            "Detected %d new anomalies across %d active recurrings",
            len(new_anomalies), len(active),
        )
        return new_anomalies

    def get_anomalies(self) -> list[RecurringAnomaly]:
        """Get all unresolved anomalies.

        Returns:
            List of unresolved RecurringAnomaly entries.
        """
        return self._model.get_anomalies(unresolved_only=True)

    def resolve_anomaly(self, anomaly_id: int) -> bool:
        """Mark an anomaly as resolved.

        Args:
            anomaly_id: The primary key of the anomaly record.

        Returns:
            True if the anomaly was resolved, False if not found.
        """
        return self._model.resolve_anomaly(anomaly_id)
