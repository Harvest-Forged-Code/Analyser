"""Budget controller for managing budget goals and financial tracking.

Provides business logic for budget management, savings calculations,
and recurring transaction detection.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

from budget_analyser.infrastructure.budget_database import (
    BudgetDatabase,
    BudgetGoal,
    EarningsGoal,
    Account,
    RecurringTransaction,
)


@dataclass
class BudgetProgress:
    """Progress tracking for a budget category."""
    
    category: str
    budget_limit: float
    spent: float
    remaining: float
    percentage: float
    status: str  # "under", "warning", "over"


@dataclass
class SavingsMetrics:
    """Savings rate and related metrics."""
    
    total_earnings: float
    total_expenses: float
    net_savings: float
    savings_rate: float  # Percentage (0-100)
    monthly_average_savings: float
    months_of_data: int


@dataclass
class NetWorthSummary:
    """Net worth summary with breakdown."""
    
    total_assets: float
    total_liabilities: float
    net_worth: float
    assets_by_type: Dict[str, float]
    liabilities_by_type: Dict[str, float]
    accounts: List[Account]


class BudgetController:
    """Controller for budget management and financial metrics."""

    def __init__(
        self,
        budget_db: BudgetDatabase,
        logger: logging.Logger | None = None
    ) -> None:
        """Initialize the budget controller.

        Args:
            budget_db: Budget database instance.
            logger: Optional logger for diagnostics.
        """
        self._budget_db = budget_db
        self._logger = logger or logging.getLogger("budget_analyser.budget_controller")

    # ==================== Budget Goals ====================

    def set_budget(self, category: str, monthly_limit: float,
                   year_month: str = "ALL") -> BudgetGoal:
        """Set a budget limit for a category."""
        return self._budget_db.set_budget_goal(category, monthly_limit, year_month)

    def get_budget(self, category: str, year_month: str = "ALL") -> Optional[BudgetGoal]:
        """Get budget for a category."""
        return self._budget_db.get_budget_goal(category, year_month)

    def get_all_budgets(self) -> List[BudgetGoal]:
        """Get all budget goals."""
        return self._budget_db.get_all_budget_goals()

    def delete_budget(self, category: str, year_month: str = "ALL") -> bool:
        """Delete a budget goal."""
        return self._budget_db.delete_budget_goal(category, year_month)

    # ==================== Earnings Goals ====================

    def set_earnings_goal(self, sub_category: str, expected_amount: float,
                          year_month: str = "ALL") -> EarningsGoal:
        """Set an expected earnings amount for a sub-category."""
        return self._budget_db.set_earnings_goal(sub_category, expected_amount, year_month)

    def get_earnings_goal(self, sub_category: str, year_month: str = "ALL") -> Optional[EarningsGoal]:
        """Get earnings goal for a sub-category."""
        return self._budget_db.get_earnings_goal(sub_category, year_month)

    def get_all_earnings_goals(self) -> List[EarningsGoal]:
        """Get all earnings goals."""
        return self._budget_db.get_all_earnings_goals()

    def delete_earnings_goal(self, sub_category: str, year_month: str = "ALL") -> bool:
        """Delete an earnings goal."""
        return self._budget_db.delete_earnings_goal(sub_category, year_month)

    def get_earnings_goal_map(self, year_month: str = "ALL") -> Dict[str, float]:
        """Get a mapping of sub-category to expected amount for easy lookup.
        
        Args:
            year_month: Specific month "YYYY-MM" or "ALL" for defaults.
            
        Returns:
            Dict mapping sub_category name to expected_amount.
        """
        goals = self._budget_db.get_all_earnings_goals()
        result: Dict[str, float] = {}
        
        # First, add all "ALL" goals
        for goal in goals:
            if goal.year_month == "ALL":
                result[goal.sub_category] = goal.expected_amount
        
        # Then override with month-specific goals if year_month is specified
        if year_month != "ALL":
            for goal in goals:
                if goal.year_month == year_month:
                    result[goal.sub_category] = goal.expected_amount
        
        return result

    def calculate_budget_progress(
        self,
        expenses_df: pd.DataFrame,
        year_month: str
    ) -> List[BudgetProgress]:
        """Calculate budget progress for all categories in a given month.

        Args:
            expenses_df: DataFrame with expense transactions.
            year_month: Month to calculate for (format: "YYYY-MM").

        Returns:
            List of BudgetProgress for each category with a budget.
        """
        budgets = self._budget_db.get_all_budget_goals()
        if not budgets:
            return []

        # Filter expenses for the month
        if expenses_df.empty:
            month_expenses = pd.DataFrame()
        else:
            df = expenses_df.copy()
            if "transaction_date" in df.columns:
                df["year_month"] = pd.to_datetime(
                    df["transaction_date"], errors="coerce"
                ).dt.strftime("%Y-%m")
                month_expenses = df[df["year_month"] == year_month]
            else:
                month_expenses = pd.DataFrame()

        # Calculate spending by category
        spending_by_category: Dict[str, float] = {}
        if not month_expenses.empty and "category" in month_expenses.columns:
            # Expenses are negative, so we negate to get positive values
            grouped = month_expenses.groupby("category")["amount"].sum()
            for cat, amount in grouped.items():
                spending_by_category[cat] = abs(float(amount))

        # Build progress for each budget
        progress_list: List[BudgetProgress] = []
        for budget in budgets:
            # Skip month-specific budgets that don't match
            if budget.year_month != "ALL" and budget.year_month != year_month:
                continue

            spent = spending_by_category.get(budget.category, 0.0)
            remaining = budget.monthly_limit - spent
            percentage = (spent / budget.monthly_limit * 100) if budget.monthly_limit > 0 else 0

            if percentage >= 100:
                status = "over"
            elif percentage >= 80:
                status = "warning"
            else:
                status = "under"

            progress_list.append(BudgetProgress(
                category=budget.category,
                budget_limit=budget.monthly_limit,
                spent=spent,
                remaining=remaining,
                percentage=percentage,
                status=status
            ))

        # Sort by percentage descending (most spent first)
        progress_list.sort(key=lambda p: p.percentage, reverse=True)
        return progress_list

    def get_categories_over_budget(
        self,
        expenses_df: pd.DataFrame,
        year_month: str
    ) -> List[BudgetProgress]:
        """Get categories that are over or near budget limit."""
        progress = self.calculate_budget_progress(expenses_df, year_month)
        return [p for p in progress if p.status in ("over", "warning")]

    # ==================== Savings Rate ====================

    def calculate_savings_metrics(
        self,
        earnings_df: pd.DataFrame,
        expenses_df: pd.DataFrame,
        year: Optional[int] = None
    ) -> SavingsMetrics:
        """Calculate savings rate and related metrics.

        Args:
            earnings_df: DataFrame with earnings transactions.
            expenses_df: DataFrame with expense transactions.
            year: Optional year to filter by. If None, uses all data.

        Returns:
            SavingsMetrics with savings rate and related data.
        """
        # Filter by year if specified
        if year is not None:
            if not earnings_df.empty and "transaction_date" in earnings_df.columns:
                earnings_df = earnings_df[
                    pd.to_datetime(earnings_df["transaction_date"], errors="coerce").dt.year == year
                ]
            if not expenses_df.empty and "transaction_date" in expenses_df.columns:
                expenses_df = expenses_df[
                    pd.to_datetime(expenses_df["transaction_date"], errors="coerce").dt.year == year
                ]

        # Calculate totals
        total_earnings = float(earnings_df["amount"].sum()) if not earnings_df.empty else 0.0
        # Expenses are negative, so we take absolute value
        total_expenses = float(abs(expenses_df["amount"].sum())) if not expenses_df.empty else 0.0

        net_savings = total_earnings - total_expenses

        # Calculate savings rate
        if total_earnings > 0:
            savings_rate = (net_savings / total_earnings) * 100
        else:
            savings_rate = 0.0

        # Calculate months of data
        months_set = set()
        for df in [earnings_df, expenses_df]:
            if not df.empty and "transaction_date" in df.columns:
                dates = pd.to_datetime(df["transaction_date"], errors="coerce")
                months_set.update(dates.dt.to_period("M").dropna().unique())

        months_of_data = len(months_set) if months_set else 1

        monthly_average_savings = net_savings / months_of_data if months_of_data > 0 else 0.0

        return SavingsMetrics(
            total_earnings=total_earnings,
            total_expenses=total_expenses,
            net_savings=net_savings,
            savings_rate=savings_rate,
            monthly_average_savings=monthly_average_savings,
            months_of_data=months_of_data
        )

    def calculate_monthly_savings(
        self,
        earnings_df: pd.DataFrame,
        expenses_df: pd.DataFrame,
        year: int
    ) -> List[Tuple[str, float, float, float, float]]:
        """Calculate savings for each month in a year.

        Args:
            earnings_df: DataFrame with earnings transactions.
            expenses_df: DataFrame with expense transactions.
            year: Year to calculate for.

        Returns:
            List of tuples: (month_name, earnings, expenses, savings, savings_rate)
        """
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        results: List[Tuple[str, float, float, float, float]] = []

        for month_idx in range(1, 13):
            year_month = f"{year}-{month_idx:02d}"

            # Filter earnings for month
            month_earnings = 0.0
            if not earnings_df.empty and "transaction_date" in earnings_df.columns:
                df = earnings_df.copy()
                df["ym"] = pd.to_datetime(df["transaction_date"], errors="coerce").dt.strftime("%Y-%m")
                month_data = df[df["ym"] == year_month]
                month_earnings = float(month_data["amount"].sum()) if not month_data.empty else 0.0

            # Filter expenses for month
            month_expenses = 0.0
            if not expenses_df.empty and "transaction_date" in expenses_df.columns:
                df = expenses_df.copy()
                df["ym"] = pd.to_datetime(df["transaction_date"], errors="coerce").dt.strftime("%Y-%m")
                month_data = df[df["ym"] == year_month]
                month_expenses = abs(float(month_data["amount"].sum())) if not month_data.empty else 0.0

            savings = month_earnings - month_expenses
            savings_rate = (savings / month_earnings * 100) if month_earnings > 0 else 0.0

            results.append((
                month_names[month_idx - 1],
                month_earnings,
                month_expenses,
                savings,
                savings_rate
            ))

        return results

    # ==================== Net Worth ====================

    def add_account(self, name: str, account_type: str, balance: float = 0,
                    notes: str = "") -> Account:
        """Add a new financial account."""
        return self._budget_db.add_account(name, account_type, balance, notes)

    def update_account_balance(self, account_id: int, balance: float) -> bool:
        """Update an account's balance."""
        return self._budget_db.update_account_balance(account_id, balance)

    def get_all_accounts(self) -> List[Account]:
        """Get all financial accounts."""
        return self._budget_db.get_all_accounts()

    def delete_account(self, account_id: int) -> bool:
        """Delete a financial account."""
        return self._budget_db.delete_account(account_id)

    def get_net_worth_summary(self) -> NetWorthSummary:
        """Get comprehensive net worth summary."""
        accounts = self._budget_db.get_all_accounts()

        assets_by_type: Dict[str, float] = {}
        liabilities_by_type: Dict[str, float] = {}

        asset_types = {"checking", "savings", "investment", "other"}
        liability_types = {"credit_card", "loan"}

        for account in accounts:
            if account.account_type in asset_types:
                assets_by_type[account.account_type] = (
                    assets_by_type.get(account.account_type, 0.0) + account.balance
                )
            elif account.account_type in liability_types:
                liabilities_by_type[account.account_type] = (
                    liabilities_by_type.get(account.account_type, 0.0) + abs(account.balance)
                )

        total_assets = sum(assets_by_type.values())
        total_liabilities = sum(liabilities_by_type.values())

        return NetWorthSummary(
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            net_worth=total_assets - total_liabilities,
            assets_by_type=assets_by_type,
            liabilities_by_type=liabilities_by_type,
            accounts=accounts
        )

    # ==================== Recurring Transactions ====================

    def add_recurring_transaction(
        self,
        description: str,
        expected_amount: float,
        frequency: str = "monthly",
        category: str = "",
        sub_category: str = ""
    ) -> RecurringTransaction:
        """Add a recurring transaction."""
        return self._budget_db.add_recurring_transaction(
            description, expected_amount, frequency, category, sub_category
        )

    def get_all_recurring_transactions(self, active_only: bool = True) -> List[RecurringTransaction]:
        """Get all recurring transactions."""
        return self._budget_db.get_all_recurring_transactions(active_only)

    def deactivate_recurring_transaction(self, recurring_id: int) -> bool:
        """Mark a recurring transaction as inactive."""
        return self._budget_db.deactivate_recurring_transaction(recurring_id)

    def delete_recurring_transaction(self, recurring_id: int) -> bool:
        """Delete a recurring transaction."""
        return self._budget_db.delete_recurring_transaction(recurring_id)

    def detect_recurring_transactions(
        self,
        transactions_df: pd.DataFrame,
        min_occurrences: int = 2
    ) -> List[dict]:
        """Detect potential recurring transactions from history."""
        return self._budget_db.detect_recurring_transactions(transactions_df, min_occurrences)

    def get_recurring_summary(
        self,
        transactions_df: pd.DataFrame
    ) -> Dict[str, float]:
        """Get summary of recurring expenses.

        Returns:
            Dictionary with monthly_total, yearly_projection, and count.
        """
        recurring = self._budget_db.get_all_recurring_transactions(active_only=True)

        monthly_total = 0.0
        for rec in recurring:
            if rec.frequency == "weekly":
                monthly_total += abs(rec.expected_amount) * 4.33
            elif rec.frequency == "monthly":
                monthly_total += abs(rec.expected_amount)
            elif rec.frequency == "quarterly":
                monthly_total += abs(rec.expected_amount) / 3
            elif rec.frequency == "yearly":
                monthly_total += abs(rec.expected_amount) / 12

        return {
            "monthly_total": monthly_total,
            "yearly_projection": monthly_total * 12,
            "count": len(recurring)
        }

    def check_recurring_anomalies(
        self,
        transactions_df: pd.DataFrame,
        tolerance_percent: float = 10.0
    ) -> List[dict]:
        """Check for anomalies in recurring transactions.

        Compares expected amounts with actual recent transactions.

        Args:
            transactions_df: DataFrame with transaction data.
            tolerance_percent: Percentage tolerance for amount variation.

        Returns:
            List of anomalies with description, expected, actual, and difference.
        """
        recurring = self._budget_db.get_all_recurring_transactions(active_only=True)
        if not recurring or transactions_df.empty:
            return []

        anomalies = []

        for rec in recurring:
            # Find recent transactions matching this recurring item
            matches = transactions_df[
                transactions_df["description"].str.contains(
                    rec.description, case=False, na=False
                )
            ]

            if matches.empty:
                continue

            # Get the most recent transaction
            if "transaction_date" in matches.columns:
                matches = matches.sort_values("transaction_date", ascending=False)

            recent_amount = abs(float(matches.iloc[0]["amount"]))
            expected_amount = abs(rec.expected_amount)

            # Check if amount differs significantly
            if expected_amount > 0:
                diff_percent = abs(recent_amount - expected_amount) / expected_amount * 100
                if diff_percent > tolerance_percent:
                    anomalies.append({
                        "description": rec.description,
                        "expected": expected_amount,
                        "actual": recent_amount,
                        "difference": recent_amount - expected_amount,
                        "difference_percent": diff_percent
                    })

        return anomalies


__all__ = [
    "BudgetProgress",
    "SavingsMetrics",
    "NetWorthSummary",
    "BudgetController",
]
