from __future__ import annotations

import logging
from typing import List

from PySide6 import QtWidgets, QtCore

from budget_analyser.controller import MapperController


class MapperPage(QtWidgets.QWidget):
    """UI-only page to edit description↔sub-category mappings.

    Features:
      - List unmapped descriptions (multi-select with filter)
      - Add selected descriptions to an existing sub-category
      - Create a new sub-category (optionally under a new category) and assign
      - Save changes to JSON mappings
    """

    refresh_requested = QtCore.Signal()

    def __init__(self, logger: logging.Logger, controller: MapperController):
        super().__init__()
        self._logger = logger
        self._controller = controller
        self._init_ui()
        self._load_data()

    # ---------- UI ----------
    def _init_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        header = QtWidgets.QLabel("Mapper")
        f = header.font()
        f.setPointSize(16)
        f.setBold(True)
        header.setFont(f)
        root.addWidget(header)

        body = QtWidgets.QHBoxLayout()
        body.setSpacing(12)
        root.addLayout(body)

        # Left: Unmapped (as rows: Date, Description, Amount) with search
        left_card = QtWidgets.QWidget()
        left_card.setObjectName("card")
        left_layout = QtWidgets.QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        left_header = QtWidgets.QHBoxLayout()
        left_header.addWidget(QtWidgets.QLabel("Unmapped Transactions"))
        left_header.addStretch(1)
        self._count_lbl = QtWidgets.QLabel("0 items")
        left_header.addWidget(self._count_lbl)
        left_layout.addLayout(left_header)

        self._filter_edit = QtWidgets.QLineEdit()
        self._filter_edit.setPlaceholderText("Filter by description...")
        self._filter_edit.textChanged.connect(self._apply_filter)
        left_layout.addWidget(self._filter_edit)

        self._table = QtWidgets.QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Date", "Description", "Amount"])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setDefaultSectionSize(26)
        left_layout.addWidget(self._table, 1)

        body.addWidget(left_card, 1)

        # Right: Actions
        right_card = QtWidgets.QWidget()
        right_card.setObjectName("card")
        right_layout = QtWidgets.QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        # Existing sub-category assignment
        group_exist = QtWidgets.QGroupBox("Add to existing sub-category")
        form1 = QtWidgets.QFormLayout(group_exist)
        self._sub_combo = QtWidgets.QComboBox()
        form1.addRow("Sub-category", self._sub_combo)
        self._btn_add_existing = QtWidgets.QPushButton("Add selected →")
        self._btn_add_existing.clicked.connect(self._on_add_existing)
        form1.addRow("", self._btn_add_existing)
        right_layout.addWidget(group_exist)

        # Create new sub-category and assign
        group_new = QtWidgets.QGroupBox("Create sub-category and assign")
        form2 = QtWidgets.QFormLayout(group_new)
        self._new_sub = QtWidgets.QLineEdit()
        self._new_sub.setPlaceholderText("e.g., coffee_shops")
        self._cat_combo = QtWidgets.QComboBox()
        self._cat_combo.setEditable(True)  # allow typing a new top-level category
        self._cat_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self._btn_create_assign = QtWidgets.QPushButton("Create & Assign →")
        self._btn_create_assign.clicked.connect(self._on_create_assign)
        form2.addRow("Sub-category", self._new_sub)
        form2.addRow("Category", self._cat_combo)
        form2.addRow("", self._btn_create_assign)
        right_layout.addWidget(group_new)

        right_layout.addStretch(1)

        # Save changes
        actions_row = QtWidgets.QHBoxLayout()
        actions_row.addStretch(1)
        self._btn_save = QtWidgets.QPushButton("Save Changes")
        self._btn_save.clicked.connect(self._on_save)
        actions_row.addWidget(self._btn_save)
        right_layout.addLayout(actions_row)

        body.addWidget(right_card, 1)

    # ---------- Data ----------
    def _load_data(self) -> None:
        # Populate combos and unmapped table
        subs = self._controller.list_sub_categories()
        self._sub_combo.clear()
        self._sub_combo.addItems(subs)

        cats = self._controller.list_categories()
        self._cat_combo.clear()
        self._cat_combo.addItems(cats)

        # Load unmapped transactions as a DataFrame
        try:
            self._unmapped_df = self._controller.list_unmapped_transactions()
        except Exception:
            # Fallback to description-only list if controller method unavailable
            descs: List[str] = self._controller.list_unmapped_descriptions()
            from pandas import DataFrame  # local import to avoid global dependency
            self._unmapped_df = DataFrame({
                "transaction_date": [],
                "description": descs,
                "amount": [],
            })
        self._render_table(self._unmapped_df)

    def _render_table(self, df) -> None:
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)
        if df is None or getattr(df, "empty", True):
            self._count_lbl.setText("0 items")
            return
        for _, row in df.iterrows():
            r = self._table.rowCount()
            self._table.insertRow(r)
            date_str = self._fmt_date(row.get("transaction_date"))
            desc = str(row.get("description", ""))
            amt_val = row.get("amount", None)
            try:
                amt_f = float(amt_val) if amt_val is not None and amt_val == amt_val else 0.0
            except Exception:
                amt_f = 0.0
            it0 = QtWidgets.QTableWidgetItem(date_str)
            it1 = QtWidgets.QTableWidgetItem(desc)
            it2 = QtWidgets.QTableWidgetItem(self._fmt_currency(amt_f))
            it2.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self._table.setItem(r, 0, it0)
            self._table.setItem(r, 1, it1)
            self._table.setItem(r, 2, it2)
        self._table.resizeColumnsToContents()
        self._table.setSortingEnabled(True)
        self._count_lbl.setText(f"{len(df.index)} items")

    # ---------- Helpers ----------
    def _selected_descriptions(self) -> List[str]:
        # Gather unique descriptions from selected rows in the table
        selected_rows = {idx.row() for idx in self._table.selectedIndexes()}
        descs: List[str] = []
        seen: set[str] = set()
        for r in sorted(selected_rows):
            item = self._table.item(r, 1)
            if item is None:
                continue
            text = item.text().strip()
            if text and text not in seen:
                seen.add(text)
                descs.append(text)
        return descs

    def _apply_filter(self, text: str) -> None:
        t = (text or "").strip().lower()
        if not t:
            self._render_table(self._unmapped_df)
            return
        try:
            mask = self._unmapped_df["description"].astype(str).str.lower().str.contains(t, na=False)
            filtered = self._unmapped_df.loc[mask]
        except Exception:
            filtered = self._unmapped_df
        self._render_table(filtered)

    # ---------- Actions ----------
    def _on_add_existing(self) -> None:
        selected = self._selected_descriptions()
        if not selected:
            QtWidgets.QMessageBox.information(self, "Mapper", "Select one or more descriptions first.")
            return
        sub = self._sub_combo.currentText().strip()
        if not sub:
            QtWidgets.QMessageBox.warning(self, "Mapper", "Choose a sub-category to assign to.")
            return
        try:
            self._controller.add_descriptions_to_sub_category(sub, selected)
        except ValueError as exc:
            # Conflict blocking per requirement
            QtWidgets.QMessageBox.warning(self, "Conflict", str(exc))
            return
        except Exception as exc:  # pragma: no cover
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to add: {exc}")
            return

        # Remove assigned from view in-memory (drop all rows with these descriptions)
        assigned = set(s.strip() for s in selected)
        try:
            self._unmapped_df = self._unmapped_df[~self._unmapped_df["description"].astype(str).isin(list(assigned))]
        except Exception:
            pass
        self._apply_filter(self._filter_edit.text())

    def _on_create_assign(self) -> None:
        selected = self._selected_descriptions()
        if not selected:
            QtWidgets.QMessageBox.information(self, "Mapper", "Select one or more descriptions first.")
            return
        new_sc = self._new_sub.text().strip()
        if not new_sc:
            QtWidgets.QMessageBox.warning(self, "Mapper", "Enter a sub-category name.")
            return
        cat = self._cat_combo.currentText().strip()
        if not cat:
            QtWidgets.QMessageBox.warning(self, "Mapper", "Enter or choose a category name.")
            return

        # To avoid partial creation on conflicts, try adding to a temporary copy logic:
        try:
            # Create sub-category first (will fail if already exists)
            self._controller.create_sub_category(new_sc, cat)
            # Then add descriptions; controller will block on conflicts
            self._controller.add_descriptions_to_sub_category(new_sc, selected)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, "Conflict", str(exc))
            # On conflict, reload mappings from store to discard the just-created subcat if needed
            try:
                self._controller.reload()
                self._load_data()
            except Exception:
                pass
            return
        except Exception as exc:  # pragma: no cover
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create/assign: {exc}")
            return

        # Update combos and table
        self._load_data()
        # Remove assigned from local df
        assigned = set(s.strip() for s in selected)
        try:
            self._unmapped_df = self._unmapped_df[~self._unmapped_df["description"].astype(str).isin(list(assigned))]
        except Exception:
            pass
        self._apply_filter(self._filter_edit.text())
        self._new_sub.clear()

    # ---------- Format helpers ----------
    @staticmethod
    def _fmt_currency(value: float) -> str:
        try:
            return f"${value:,.2f}"
        except Exception:
            return str(value)

    @staticmethod
    def _fmt_date(value) -> str:
        try:
            if hasattr(value, "date"):
                return str(value.date())
            s = str(value)
            return s[:10]
        except Exception:  # pragma: no cover
            return str(value)[:10]

    def _on_save(self) -> None:
        try:
            self._controller.save()
            QtWidgets.QMessageBox.information(self, "Mapper", "Changes saved.")
            self.refresh_requested.emit()
        except Exception as exc:  # pragma: no cover
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save: {exc}")
