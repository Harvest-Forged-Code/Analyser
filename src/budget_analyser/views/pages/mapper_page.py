from __future__ import annotations

import logging
from typing import List

from PySide6 import QtWidgets, QtCore

from budget_analyser.controller import MapperController
from budget_analyser.views.pages._page_base import ModernPageMixin


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
            title="Transaction Mapper",
            subtitle="Map unmapped transactions to categories and sub-categories",
            icon="🧭"
        )
        root.addWidget(page_header)

        # Two-column layout
        body = QtWidgets.QHBoxLayout()
        body.setSpacing(16)

        # Left card: Unmapped Transactions
        left_card, left_layout = ModernPageMixin.create_card("UNMAPPED TRANSACTIONS")

        # Count label
        count_row = QtWidgets.QHBoxLayout()
        count_row.addStretch(1)
        self._count_lbl = QtWidgets.QLabel("0 items")
        self._count_lbl.setStyleSheet("font-size: 12px; color: #9CA3AF; font-weight: 600;")
        count_row.addWidget(self._count_lbl)
        left_layout.addLayout(count_row)

        # Filter
        filter_label = ModernPageMixin.create_control_label("Filter")
        left_layout.addWidget(filter_label)

        self._filter_edit = QtWidgets.QLineEdit()
        self._filter_edit.setPlaceholderText("Filter by description...")
        self._filter_edit.setMinimumHeight(34)
        self._filter_edit.textChanged.connect(self._apply_filter)
        left_layout.addWidget(self._filter_edit)

        # Table
        self._table = QtWidgets.QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Date", "Description", "Amount"])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setDefaultSectionSize(34)
        left_layout.addWidget(self._table, 1)

        body.addWidget(left_card, 1)

        # Right card: Actions
        right_card, right_layout = ModernPageMixin.create_card("MAPPING ACTIONS")

        # Existing sub-category section
        existing_section = QtWidgets.QWidget()
        existing_layout = QtWidgets.QVBoxLayout(existing_section)
        existing_layout.setContentsMargins(0, 0, 0, 0)
        existing_layout.setSpacing(16)

        section_label1 = QtWidgets.QLabel("ADD TO EXISTING SUB-CATEGORY")
        section_label1.setStyleSheet("font-size: 11px; font-weight: 700; color: #8B5CF6; letter-spacing: 0.8px;")
        existing_layout.addWidget(section_label1)

        sub_label = ModernPageMixin.create_control_label("Sub-category")
        existing_layout.addWidget(sub_label)

        self._sub_combo = QtWidgets.QComboBox()
        ModernPageMixin.style_combo_box(self._sub_combo)
        existing_layout.addWidget(self._sub_combo)

        self._btn_add_existing = ModernPageMixin.create_action_button("Add Selected →", primary=True)
        self._btn_add_existing.clicked.connect(self._on_add_existing)
        existing_layout.addWidget(self._btn_add_existing)

        right_layout.addWidget(existing_section)

        # Separator
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setStyleSheet("background: rgba(80, 80, 90, 0.3); max-height: 1px;")
        right_layout.addWidget(separator)

        # Create new sub-category section
        new_section = QtWidgets.QWidget()
        new_layout = QtWidgets.QVBoxLayout(new_section)
        new_layout.setContentsMargins(0, 0, 0, 0)
        new_layout.setSpacing(16)

        section_label2 = QtWidgets.QLabel("CREATE NEW SUB-CATEGORY")
        section_label2.setStyleSheet("font-size: 11px; font-weight: 700; color: #8B5CF6; letter-spacing: 0.8px;")
        new_layout.addWidget(section_label2)

        new_sub_label = ModernPageMixin.create_control_label("Sub-category Name")
        new_layout.addWidget(new_sub_label)

        self._new_sub = QtWidgets.QLineEdit()
        self._new_sub.setPlaceholderText("e.g., coffee_shops")
        self._new_sub.setMinimumHeight(34)
        new_layout.addWidget(self._new_sub)

        cat_label = ModernPageMixin.create_control_label("Category")
        new_layout.addWidget(cat_label)

        self._cat_combo = QtWidgets.QComboBox()
        self._cat_combo.setEditable(True)
        self._cat_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        ModernPageMixin.style_combo_box(self._cat_combo)
        new_layout.addWidget(self._cat_combo)

        self._btn_create_assign = ModernPageMixin.create_action_button("Create & Assign →", primary=True)
        self._btn_create_assign.clicked.connect(self._on_create_assign)
        new_layout.addWidget(self._btn_create_assign)

        right_layout.addWidget(new_section)

        right_layout.addStretch(1)

        # Save button
        self._btn_save = ModernPageMixin.create_action_button("Save Changes", primary=True)
        self._btn_save.setMinimumHeight(48)
        self._btn_save.clicked.connect(self._on_save)
        right_layout.addWidget(self._btn_save)

        body.addWidget(right_card, 1)
        root.addLayout(body, 1)

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
