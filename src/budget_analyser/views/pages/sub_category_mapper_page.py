from __future__ import annotations

import logging
from typing import List

from PySide6 import QtCore, QtWidgets

from budget_analyser.controller import SubCategoryMapperController
from budget_analyser.views.pages._page_base import ModernPageMixin


class SubCategoryMapperPage(QtWidgets.QWidget):
    """UI to rearrange sub-categories within categories and add new ones."""

    refresh_requested = QtCore.Signal()

    def __init__(self, logger: logging.Logger, controller: SubCategoryMapperController):
        super().__init__()
        self._logger = logger
        self._controller = controller
        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        # Scroll area for content
        scroll, container = ModernPageMixin.create_scroll_area()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        root = QtWidgets.QVBoxLayout(container)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)

        # Page header
        page_header = ModernPageMixin.create_page_header(
            title="Sub-Category Mapping",
            subtitle="Move sub-categories between categories or add new ones",
            icon="🔀"
        )
        root.addWidget(page_header)

        # Three-column layout for source/target panels
        body = QtWidgets.QHBoxLayout()
        body.setSpacing(16)

        self._source_card, self._source_combo, self._source_list = self._build_category_panel("SOURCE CATEGORY")
        self._target_card, self._target_combo, self._target_list = self._build_category_panel("TARGET CATEGORY")

        body.addWidget(self._source_card, 1)

        # Middle controls
        mid = QtWidgets.QVBoxLayout()
        mid.setSpacing(12)
        mid.addStretch(1)

        self._btn_to_target = ModernPageMixin.create_action_button("→ Move to Target", primary=False)
        self._btn_to_target.clicked.connect(self._on_move_to_target)
        mid.addWidget(self._btn_to_target)

        self._btn_to_source = ModernPageMixin.create_action_button("← Move to Source", primary=False)
        self._btn_to_source.clicked.connect(self._on_move_to_source)
        mid.addWidget(self._btn_to_source)

        mid.addStretch(1)
        body.addLayout(mid)

        body.addWidget(self._target_card, 1)

        root.addLayout(body, 1)

        # Add sub-category card
        add_card, add_layout = ModernPageMixin.create_card("ADD NEW SUB-CATEGORY")

        name_label = ModernPageMixin.create_control_label("Sub-category Name")
        add_layout.addWidget(name_label)

        self._new_sub = QtWidgets.QLineEdit()
        self._new_sub.setPlaceholderText("e.g., coffee_shops")
        self._new_sub.setMinimumHeight(34)
        add_layout.addWidget(self._new_sub)

        cat_label = ModernPageMixin.create_control_label("Category")
        add_layout.addWidget(cat_label)

        self._add_combo = QtWidgets.QComboBox()
        self._add_combo.setEditable(True)
        self._add_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        ModernPageMixin.style_combo_box(self._add_combo)
        add_layout.addWidget(self._add_combo)

        self._btn_add = ModernPageMixin.create_action_button("Add Sub-category", primary=True)
        self._btn_add.clicked.connect(self._on_add)
        add_layout.addWidget(self._btn_add)

        root.addWidget(add_card)

        # Action buttons
        actions = QtWidgets.QHBoxLayout()
        actions.addStretch(1)

        self._btn_reset = ModernPageMixin.create_action_button("Reset", primary=False)
        self._btn_reset.clicked.connect(self._on_reset)
        actions.addWidget(self._btn_reset)

        self._btn_save = ModernPageMixin.create_action_button("Save Changes", primary=True)
        self._btn_save.setMinimumHeight(48)
        self._btn_save.clicked.connect(self._on_save)
        actions.addWidget(self._btn_save)

        root.addLayout(actions)

    def _build_category_panel(self, title: str) -> tuple[QtWidgets.QWidget, QtWidgets.QComboBox, QtWidgets.QListWidget]:
        card, layout = ModernPageMixin.create_card(title)

        cat_label = ModernPageMixin.create_control_label("Select Category")
        layout.addWidget(cat_label)

        combo = QtWidgets.QComboBox()
        combo.setEditable(False)
        combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        combo.currentIndexChanged.connect(self._on_combo_changed)
        ModernPageMixin.style_combo_box(combo)
        layout.addWidget(combo)

        lst = QtWidgets.QListWidget()
        lst.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        lst.setAlternatingRowColors(True)
        lst.setSpacing(2)
        layout.addWidget(lst, 1)

        hint = QtWidgets.QLabel("Select a category to view and move its sub-categories")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 11px; color: #9CA3AF; font-style: italic;")
        layout.addWidget(hint)

        return card, combo, lst

    # ---- Data helpers ----
    def _set_combo_options(self, combo: QtWidgets.QComboBox, categories: List[str], selected: str | None = None) -> None:
        current = combo.currentText().strip()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(categories)
        if selected:
            idx = combo.findText(selected, QtCore.Qt.MatchFlag.MatchFixedString)
            combo.setCurrentIndex(idx if idx >= 0 else -1)
        elif current:
            idx = combo.findText(current, QtCore.Qt.MatchFlag.MatchFixedString)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)

    def _load_data(self) -> None:
        categories = sorted(self._controller.categories(), key=lambda s: s.lower())
        self._set_combo_options(self._source_combo, categories)
        self._set_combo_options(self._target_combo, categories)
        self._set_combo_options(self._add_combo, categories)

        # Default selections
        if self._source_combo.count() > 0 and self._source_combo.currentIndex() < 0:
            self._source_combo.setCurrentIndex(0)
        if self._target_combo.count() > 1 and self._target_combo.currentIndex() < 0:
            self._target_combo.setCurrentIndex(1)
        elif self._target_combo.count() > 0 and self._target_combo.currentIndex() < 0:
            self._target_combo.setCurrentIndex(0)

        self._refresh_lists()

    def _refresh_lists(self) -> None:
        src_cat = self._source_combo.currentText().strip()
        tgt_cat = self._target_combo.currentText().strip()
        self._populate(self._source_list, self._controller.sub_categories(src_cat) if src_cat else [])
        self._populate(self._target_list, self._controller.sub_categories(tgt_cat) if tgt_cat else [])

    @staticmethod
    def _populate(widget: QtWidgets.QListWidget, items: List[str]) -> None:
        widget.setSortingEnabled(False)
        widget.clear()
        for item in items:
            if not str(item).strip():
                continue
            widget.addItem(str(item).strip())
        widget.setSortingEnabled(True)

    # ---- Actions ----
    def _on_combo_changed(self) -> None:
        self._refresh_lists()

    def _selected_items(self, widget: QtWidgets.QListWidget) -> List[str]:
        selected = []
        for itm in widget.selectedItems():
            text = itm.text().strip()
            if text:
                selected.append(text)
        return selected

    def _on_move_to_target(self) -> None:
        source = self._source_combo.currentText().strip()
        target = self._target_combo.currentText().strip()
        selected = self._selected_items(self._source_list)
        if not selected or not source or not target:
            return
        self._controller.move_sub_categories(selected, source, target)
        self._refresh_lists()

    def _on_move_to_source(self) -> None:
        source = self._target_combo.currentText().strip()
        target = self._source_combo.currentText().strip()
        selected = self._selected_items(self._target_list)
        if not selected or not source or not target:
            return
        self._controller.move_sub_categories(selected, source, target)
        self._refresh_lists()

    def _on_add(self) -> None:
        name = self._new_sub.text().strip()
        cat = self._add_combo.currentText().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Sub-category Mapping", "Enter a sub-category name.")
            return
        if not cat:
            QtWidgets.QMessageBox.warning(self, "Sub-category Mapping", "Enter a category name.")
            return
        try:
            self._controller.add_sub_category(name, cat)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Sub-category Mapping", str(exc))
            return
        self._new_sub.clear()
        self._load_data()
        # Focus on the category we just updated
        idx = self._source_combo.findText(cat, QtCore.Qt.MatchFlag.MatchFixedString)
        if idx >= 0:
            self._source_combo.setCurrentIndex(idx)
        idx_tgt = self._target_combo.findText(cat, QtCore.Qt.MatchFlag.MatchFixedString)
        if idx_tgt >= 0:
            self._target_combo.setCurrentIndex(idx_tgt)

    def _on_save(self) -> None:
        try:
            self._controller.save()
            QtWidgets.QMessageBox.information(self, "Sub-category Mapping", "Mapping saved.")
            self.refresh_requested.emit()
        except Exception as exc:  # pragma: no cover
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save: {exc}")

    def _on_reset(self) -> None:
        self._controller.reload()
        self._load_data()