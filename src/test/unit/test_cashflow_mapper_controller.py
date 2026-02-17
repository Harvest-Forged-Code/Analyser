from __future__ import annotations

import logging

from budget_analyser.controller.cashflow_mapper_controller import CashflowMapperController


class _StubStore:
    def __init__(self, mapping):
        self.mapping = mapping
        self.saved = None

    def load_cashflow(self):
        return self.mapping

    def save_cashflow(self, mapping):
        self.saved = mapping
        self.mapping = mapping


def test_set_mapping_dedup_and_expenses_win() -> None:
    store = _StubStore({"Earnings": ["Income", "Bonus"], "Expenses": ["Flexible"]})
    controller = CashflowMapperController(store, logging.getLogger(__name__))

    controller.set_mapping(["Income", "Flexible", "Bonus", "Bonus"], ["Flexible", "Needs"])

    assert controller.earnings_categories() == ["Income", "Bonus"]
    assert controller.expense_categories() == ["Flexible", "Needs"]


def test_move_and_save_persists_changes() -> None:
    store = _StubStore({"Earnings": ["Income"], "Expenses": ["Needs"]})
    controller = CashflowMapperController(store, logging.getLogger(__name__))

    controller.move_to_expenses(["Income"])
    controller.add_category("Refunded_money", "Expenses")
    controller.save()

    assert store.saved is not None
    assert store.saved["Expenses"] == ["Needs", "Income", "Refunded_money"]
    assert store.saved["Earnings"] == []