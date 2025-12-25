from __future__ import annotations

import logging

from budget_analyser.controller.sub_category_mapper_controller import SubCategoryMapperController


class _StubStore:
    def __init__(self, mapping):
        self.mapping = mapping
        self.saved = None

    def load_sub_to_cat(self):
        return self.mapping

    def save_sub_to_cat(self, mapping):
        self.saved = mapping
        self.mapping = mapping


def test_move_between_categories_and_dedup() -> None:
    store = _StubStore({"Needs": ["Groceries", "Rent"], "Flexible": ["Travel", "Groceries"]})
    controller = SubCategoryMapperController(store, logging.getLogger(__name__))

    controller.move_sub_categories(["Travel", "Groceries"], "Flexible", "Needs")

    assert controller.sub_categories("Needs") == ["Groceries", "Rent", "Travel"]
    assert controller.sub_categories("Flexible") == []


def test_add_creates_category_and_removes_from_others() -> None:
    store = _StubStore({"Luxuries": ["Travel"], "Flexible": ["Travel"]})
    controller = SubCategoryMapperController(store, logging.getLogger(__name__))

    controller.add_sub_category("Coffee", "Needs")
    controller.add_sub_category("Travel", "Needs")

    assert "Needs" in controller.categories()
    assert controller.sub_categories("Needs") == ["Coffee", "Travel"]
    # Travel removed from other categories
    assert controller.sub_categories("Luxuries") == []
    assert controller.sub_categories("Flexible") == []


def test_save_persists_mapping() -> None:
    store = _StubStore({"Needs": ["Groceries"]})
    controller = SubCategoryMapperController(store, logging.getLogger(__name__))

    controller.add_sub_category("Rent", "Needs")
    controller.save()

    assert store.saved is not None
    assert store.saved["Needs"] == ["Groceries", "Rent"]