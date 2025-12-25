from __future__ import annotations

import logging
from typing import List

from PySide6 import QtCore, QtWidgets

from budget_analyser.controller import SubCategoryMapperController


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
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QtWidgets.QLabel("Sub-category Mapping")
        tf = title.font()
        tf.setPointSize(16)
        tf.setBold(True)
        title.setFont(tf)
        root.addWidget(title)

        helper = QtWidgets.QLabel(
            "Move sub-categories between categories or add new ones. "
            "Changes are saved to the sub_category_to_category mapping JSON."
        )
        helper.setWordWrap(True)
        root.addWidget(helper)

        body = QtWidgets.QHBoxLayout()
        body.setSpacing(10)
        root.addLayout(body)

        self._source_card, self._source_combo, self._source_list = self._build_category_panel("Source Category")
        self._target_card, self._target_combo, self._target_list = self._build_category_panel("Target Category")

        body.addWidget(self._source_card, 1)

        mid = QtWidgets.QVBoxLayout()
        mid.setSpacing(8)
        self._btn_to_target = QtWidgets.QPushButton("→ Move to target")
        self._btn_to_target.clicked.connect(self._on_move_to_target)
        self._btn_to_source = QtWidgets.QPushButton("← Move to source")
        self._btn_to_source.clicked.connect(self._on_move_to_source)
        mid.addStretch(1)
        mid.addWidget(self._btn_to_target)
        mid.addWidget(self._btn_to_source)
        mid.addStretch(1)
        body.addLayout(mid)

        body.addWidget(self._target_card, 1)

        # Add sub-category
        add_box = QtWidgets.QGroupBox("Add sub-category")
        add_layout = QtWidgets.QFormLayout(add_box)
        self._new_sub = QtWidgets.QLineEdit()
        self._new_sub.setPlaceholderText("e.g., coffee_shops")
        self._add_combo = QtWidgets.QComboBox()
        self._add_combo.setEditable(True)
        self._add_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self._btn_add = QtWidgets.QPushButton("Add")
        self._btn_add.clicked.connect(self._on_add)
        add_layout.addRow("Name", self._new_sub)
        add_layout.addRow("Category", self._add_combo)
        add_layout.addRow("", self._btn_add)
        root.addWidget(add_box)

        # Save/reset actions
        actions = QtWidgets.QHBoxLayout()
        actions.addStretch(1)
        self._btn_reset = QtWidgets.QPushButton("Reset")
        self._btn_reset.clicked.connect(self._on_reset)
        self._btn_save = QtWidgets.QPushButton("Save Changes")
        self._btn_save.clicked.connect(self._on_save)
        actions.addWidget(self._btn_reset)
        actions.addWidget(self._btn_save)
        root.addLayout(actions)

    def _build_category_panel(self, title: str) -> tuple[QtWidgets.QWidget, QtWidgets.QComboBox, QtWidgets.QListWidget]:
        card = QtWidgets.QWidget()
        card.setObjectName("card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        lbl = QtWidgets.QLabel(title)
        lf = lbl.font()
        lf.setBold(True)
        lbl.setFont(lf)
        layout.addWidget(lbl)

        combo = QtWidgets.QComboBox()
        combo.setEditable(False)
        combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        combo.currentIndexChanged.connect(self._on_combo_changed)
        layout.addWidget(combo)

        lst = QtWidgets.QListWidget()
        lst.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        lst.setAlternatingRowColors(True)
        lst.setSpacing(2)
        layout.addWidget(lst, 1)

        hint = QtWidgets.QLabel("Select a category to view and move its sub-categories.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #94A3B8;")
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