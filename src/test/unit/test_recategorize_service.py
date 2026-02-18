"""Unit tests for features.recategorize.service."""

from __future__ import annotations

import pandas as pd

from budget_analyser.features.ingestion.categorization import CategoryMappers
from budget_analyser.features.recategorize.service import (
    RecategorizeService,
    RecategorizeResult,
)


def _make_mappers() -> CategoryMappers:
    return CategoryMappers(
        description_to_sub_category={
            "Dining": ["STARBUCKS", "CHIPOTLE"],
            "Groceries": ["WALMART", "COSTCO"],
        },
        sub_category_to_category={
            "Wants": ["Dining"],
            "Needs": ["Groceries"],
        },
    )


class TestRecategorizeService:
    """Tests for RecategorizeService."""

    def test_empty_transactions(self) -> None:
        svc = RecategorizeService(category_mappers=_make_mappers())
        updated_df, result = svc.recategorize(
            transactions=pd.DataFrame(),
        )
        assert result.success
        assert result.total_transactions == 0
        assert result.updated_count == 0
        assert updated_df.empty

    def test_no_changes_needed(self) -> None:
        svc = RecategorizeService(category_mappers=_make_mappers())
        df = pd.DataFrame({
            "description": ["STARBUCKS COFFEE"],
            "sub_category": ["Dining"],
            "category": ["Wants"],
            "amount": [-5.0],
            "from_account": ["citi"],
            "transaction_date": ["2024-01-15"],
        })
        updated_df, result = svc.recategorize(transactions=df)
        assert result.success
        assert result.total_transactions == 1
        assert result.updated_count == 0
        assert updated_df.empty

    def test_detects_changed_sub_category(self) -> None:
        svc = RecategorizeService(category_mappers=_make_mappers())
        df = pd.DataFrame({
            "description": ["STARBUCKS COFFEE"],
            "sub_category": ["OldCategory"],
            "category": ["OldParent"],
            "amount": [-5.0],
            "from_account": ["citi"],
            "transaction_date": ["2024-01-15"],
        })
        updated_df, result = svc.recategorize(transactions=df)
        assert result.success
        assert result.updated_count == 1
        assert updated_df.iloc[0]["sub_category"] == "Dining"
        assert updated_df.iloc[0]["category"] == "Wants"

    def test_detects_changed_category_only(self) -> None:
        svc = RecategorizeService(category_mappers=_make_mappers())
        df = pd.DataFrame({
            "description": ["COSTCO WHSE"],
            "sub_category": ["Groceries"],
            "category": ["WrongParent"],
            "amount": [-50.0],
            "from_account": ["citi"],
            "transaction_date": ["2024-01-15"],
        })
        updated_df, result = svc.recategorize(transactions=df)
        assert result.success
        assert result.updated_count == 1
        assert updated_df.iloc[0]["category"] == "Needs"

    def test_mixed_changed_and_unchanged(self) -> None:
        svc = RecategorizeService(category_mappers=_make_mappers())
        df = pd.DataFrame({
            "description": [
                "STARBUCKS COFFEE",
                "WALMART STORE",
            ],
            "sub_category": ["Dining", "OldSub"],
            "category": ["Wants", "OldCat"],
            "amount": [-5.0, -30.0],
            "from_account": ["citi", "citi"],
            "transaction_date": ["2024-01-15", "2024-01-16"],
        })
        updated_df, result = svc.recategorize(transactions=df)
        assert result.success
        assert result.total_transactions == 2
        assert result.updated_count == 1
        assert updated_df.iloc[0]["sub_category"] == "Groceries"

    def test_result_message_format(self) -> None:
        svc = RecategorizeService(category_mappers=_make_mappers())
        df = pd.DataFrame({
            "description": ["STARBUCKS"],
            "sub_category": ["Old"],
            "category": ["Old"],
            "amount": [-5.0],
            "from_account": ["acc"],
            "transaction_date": ["2024-01-01"],
        })
        _, result = svc.recategorize(transactions=df)
        assert "1 of 1" in result.message
