from __future__ import annotations

import logging
from typing import List

from PySide6 import QtCore, QtWidgets

from budget_analyser.controller import CashflowMapperController


class CashflowMapperPage(QtWidgets.QWidget):
    """UI to edit earnings/expenses category mapping with drag/drop."""

    refresh_requested = QtCore.Signal()

    def __init__(self, logger: logging.Logger, controller: CashflowMapperController):
        super().__init__()
        self._logger = logger
        self._controller = controller
        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QtWidgets.QLabel("Cashflow Mapping")
        tf = title.font()
        tf.setPointSize(16)
        tf.setBold(True)
        title.setFont(tf)
        root.addWidget(title)

        helper = QtWidgets.QLabel(
            "Drag categories between Earnings and Expenses or use the move buttons."
            " Add new categories to the desired group, then save to update the mapping JSON."
        )
        helper.setWordWrap(True)
        root.addWidget(helper)

        body = QtWidgets.QHBoxLayout()
        body.setSpacing(10)
        root.addLayout(body)

        self._earnings_list = self._build_list("Earnings")
        self._expenses_list = self._build_list("Expenses")

        body.addWidget(self._earnings_list[0], 1)

        # Middle controls
        mid = QtWidgets.QVBoxLayout()
        mid.setSpacing(8)
        self._btn_to_expenses = QtWidgets.QPushButton("→ To Expenses")
        self._btn_to_expenses.clicked.connect(self._move_to_expenses)
        self._btn_to_earnings = QtWidgets.QPushButton("← To Earnings")
        self._btn_to_earnings.clicked.connect(self._move_to_earnings)
        mid.addStretch(1)
        mid.addWidget(self._btn_to_expenses)
        mid.addWidget(self._btn_to_earnings)
        mid.addStretch(1)
        body.addLayout(mid)

        body.addWidget(self._expenses_list[0], 1)

        # Add category row
        add_box = QtWidgets.QGroupBox("Add category")
        add_layout = QtWidgets.QFormLayout(add_box)
        self._new_category = QtWidgets.QLineEdit()
        self._new_category.setPlaceholderText("e.g., Reimbursements")
        self._flow_combo = QtWidgets.QComboBox()
        self._flow_combo.addItems(["Earnings", "Expenses"])
        self._btn_add = QtWidgets.QPushButton("Add")
        self._btn_add.clicked.connect(self._on_add)
        add_layout.addRow("Name", self._new_category)
        add_layout.addRow("Group", self._flow_combo)
        add_layout.addRow("", self._btn_add)
        root.addWidget(add_box)

        # Save/reset actions
        actions = QtWidgets.QHBoxLayout()
        actions.addStretch(1)
        self._btn_reset = QtWidgets.QPushButton("Reset")
        self._btn_reset.clicked.connect(self._load_data)
        self._btn_save = QtWidgets.QPushButton("Save Changes")
        self._btn_save.clicked.connect(self._on_save)
        actions.addWidget(self._btn_reset)
        actions.addWidget(self._btn_save)
        root.addLayout(actions)

    def _build_list(self, title: str) -> tuple[QtWidgets.QWidget, QtWidgets.QListWidget]:
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

        lst = QtWidgets.QListWidget()
        lst.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        lst.setDragEnabled(True)
        lst.setAcceptDrops(True)
        lst.setDropIndicatorShown(True)
        lst.setDefaultDropAction(QtCore.Qt.MoveAction)
        lst.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        lst.setAlternatingRowColors(True)
        lst.setSpacing(2)
        layout.addWidget(lst, 1)

        hint = QtWidgets.QLabel("Drag items or use the arrows to move between groups.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #94A3B8;")
        layout.addWidget(hint)

        return card, lst

    # ---- Data helpers ----
    def _load_data(self) -> None:
        try:
            mapping = self._controller.mapping()
        except Exception as exc:  # pragma: no cover
            mapping = {"Earnings": [], "Expenses": []}
            try:
                self._logger.exception("Failed to load cashflow mapping: %s", exc)
            except Exception:
                pass

        self._populate(self._earnings_list[1], mapping.get("Earnings", []))
        self._populate(self._expenses_list[1], mapping.get("Expenses", []))

    @staticmethod
    def _populate(widget: QtWidgets.QListWidget, items: List[str]) -> None:
        widget.clear()
        for item in items:
            if not str(item).strip():
                continue
            widget.addItem(str(item).strip())

    # ---- Actions ----
    def _collect_items(self, widget: QtWidgets.QListWidget) -> List[str]:
        return [widget.item(i).text().strip() for i in range(widget.count()) if widget.item(i)]

    def _move_to_expenses(self) -> None:
        selected = [i.text() for i in self._earnings_list[1].selectedItems()]
        if not selected:
            return
        for item in selected:
            self._expenses_list[1].addItem(item)
        for item in reversed(self._earnings_list[1].selectedItems()):
            self._earnings_list[1].takeItem(self._earnings_list[1].row(item))

    def _move_to_earnings(self) -> None:
        selected = [i.text() for i in self._expenses_list[1].selectedItems()]
        if not selected:
            return
        for item in selected:
            self._earnings_list[1].addItem(item)
        for item in reversed(self._expenses_list[1].selectedItems()):
            self._expenses_list[1].takeItem(self._expenses_list[1].row(item))

    def _on_add(self) -> None:
        name = self._new_category.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Cashflow Mapping", "Enter a category name.")
            return
        target = self._flow_combo.currentText()
        # Avoid immediate duplicates in UI
        target_list = self._earnings_list[1] if target.lower().startswith("earn") else self._expenses_list[1]
        existing = {target_list.item(i).text().strip().lower() for i in range(target_list.count())}
        other_list = self._expenses_list[1] if target_list is self._earnings_list[1] else self._earnings_list[1]
        # Remove from other list if present
        for i in reversed(range(other_list.count())):
            if other_list.item(i).text().strip().lower() == name.lower():
                other_list.takeItem(i)
        if name.lower() not in existing:
            target_list.addItem(name)
        self._new_category.clear()

    def _sync_controller_from_lists(self) -> None:
        earnings = self._collect_items(self._earnings_list[1])
        expenses = self._collect_items(self._expenses_list[1])
        self._controller.set_mapping(earnings, expenses)

    def _on_save(self) -> None:
        self._sync_controller_from_lists()
        try:
            self._controller.save()
            QtWidgets.QMessageBox.information(self, "Cashflow Mapping", "Mapping saved.")
            self.refresh_requested.emit()
        except Exception as exc:  # pragma: no cover
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save: {exc}")
