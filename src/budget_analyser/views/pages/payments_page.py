from __future__ import annotations

import logging
from typing import List

from PySide6 import QtCore, QtWidgets

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.controller import PaymentsReconciliationController
from budget_analyser.views.pages._page_base import ModernPageMixin


class PaymentsPage(QtWidgets.QWidget):
    """Payments Reconciliation page.

    UI-only: compares Payments Made vs Payment Confirmations per month.
    Two side-by-side tables and a summary bar with totals and difference.
    """

    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        super().__init__()
        self._reports = reports
        self._logger = logger
        self._controller = PaymentsReconciliationController(reports, logger)

        self._current_period = None  # type: ignore[var-annotated]
        self._init_ui()

    def _init_ui(self) -> None:
        # Scroll area for content
        scroll, container = ModernPageMixin.create_scroll_area()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        root = QtWidgets.QVBoxLayout(container)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)

        # Header with month selector
        header_container = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)

        # Page header
        page_header = ModernPageMixin.create_page_header(
            title="Payments Reconciliation",
            subtitle="Compare payments made vs payment confirmations",
            icon="🔁"
        )
        header_layout.addWidget(page_header, 1)

        # Month selector
        month_container = QtWidgets.QWidget()
        month_layout = QtWidgets.QVBoxLayout(month_container)
        month_layout.setContentsMargins(0, 0, 0, 0)
        month_layout.setSpacing(8)

        month_label = ModernPageMixin.create_control_label("Month")
        month_layout.addWidget(month_label)

        self.month_combo = QtWidgets.QComboBox()
        ModernPageMixin.style_combo_box(self.month_combo, min_height=44)
        self.month_combo.setMinimumWidth(180)
        month_layout.addWidget(self.month_combo)

        header_layout.addWidget(month_container)
        root.addWidget(header_container)

        # Two-column cards layout
        tables_row = QtWidgets.QHBoxLayout()
        tables_row.setSpacing(16)

        # Left card - Payments Made
        left_card, left_layout = ModernPageMixin.create_card("PAYMENTS MADE")

        # Totals row
        left_totals = QtWidgets.QHBoxLayout()
        self.left_count = QtWidgets.QLabel("0 items")
        self.left_count.setStyleSheet("font-size: 12px; color: #9CA3AF; font-weight: 600;")
        left_totals.addWidget(self.left_count)
        left_totals.addStretch(1)
        self.left_total = QtWidgets.QLabel("$0.00")
        self.left_total.setStyleSheet("font-size: 18px; font-weight: 700; color: #EF4444;")
        left_totals.addWidget(self.left_total)
        left_layout.addLayout(left_totals)

        self.table_left = QtWidgets.QTableWidget(0, 5)
        self.table_left.setHorizontalHeaderLabels([
            "Date",
            "Description",
            "Amount",
            "From Account",
            "Category/Sub",
        ])
        self._prep_table(self.table_left)
        left_layout.addWidget(self.table_left, 1)

        # Right card - Payment Confirmations
        right_card, right_layout = ModernPageMixin.create_card("PAYMENT CONFIRMATIONS")

        # Totals row
        right_totals = QtWidgets.QHBoxLayout()
        self.right_count = QtWidgets.QLabel("0 items")
        self.right_count.setStyleSheet("font-size: 12px; color: #9CA3AF; font-weight: 600;")
        right_totals.addWidget(self.right_count)
        right_totals.addStretch(1)
        self.right_total = QtWidgets.QLabel("$0.00")
        self.right_total.setStyleSheet("font-size: 18px; font-weight: 700; color: #10B981;")
        right_totals.addWidget(self.right_total)
        right_layout.addLayout(right_totals)

        self.table_right = QtWidgets.QTableWidget(0, 5)
        self.table_right.setHorizontalHeaderLabels([
            "Date",
            "Description",
            "Amount",
            "From Account",
            "Category/Sub",
        ])
        self._prep_table(self.table_right)
        right_layout.addWidget(self.table_right, 1)

        tables_row.addWidget(left_card, 1)
        tables_row.addWidget(right_card, 1)
        root.addLayout(tables_row, 1)

        # Summary card
        summary_card, summary_layout = ModernPageMixin.create_card("RECONCILIATION SUMMARY")
        self.sum_label = QtWidgets.QLabel("Totals: Payments $0.00 | Confirmations $0.00 | Diff $0.00")
        self.sum_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #E2E4F0;")
        summary_layout.addWidget(self.sum_label)
        root.addWidget(summary_card)

        # Populate months and wire
        self._populate_months()
        self.month_combo.currentIndexChanged.connect(self._on_month_changed)
        if self.month_combo.count() > 0:
            self.month_combo.setCurrentIndex(self.month_combo.count() - 1)

    @staticmethod
    def _prep_table(tbl: QtWidgets.QTableWidget) -> None:
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        tbl.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setDefaultSectionSize(34)

    def _populate_months(self) -> None:
        self.month_combo.clear()
        for p in self._controller.available_months():
            self.month_combo.addItem(self._controller.month_label(p), userData=p)

    def _on_month_changed(self, index: int) -> None:
        period = self.month_combo.currentData()
        self._current_period = period
        if period is None:
            return
        self._logger.info("PaymentsPage: Month changed -> %s", period)
        summary = self._controller.data(period)
        self._refresh_tables(summary)

    def _refresh_tables(self, summary) -> None:
        # Left
        self._fill_table(self.table_left, summary.payments_made)
        self.left_count.setText(f"{len(summary.payments_made.index)} items")
        self.left_total.setText(self._fmt_currency(summary.total_payments_made))
        # Right
        self._fill_table(self.table_right, summary.payment_confirmations)
        self.right_count.setText(f"{len(summary.payment_confirmations.index)} items")
        self.right_total.setText(self._fmt_currency(summary.total_payment_confirmations))
        # Summary text and mismatch highlight
        diff = summary.difference
        self.sum_label.setText(
            f"Totals: Payments {self._fmt_currency(summary.total_payments_made)} | "
            f"Confirmations {self._fmt_currency(summary.total_payment_confirmations)} | "
            f"Diff {self._fmt_currency(diff)}"
        )

    def _fill_table(self, table: QtWidgets.QTableWidget, df) -> None:
        table.setSortingEnabled(False)
        table.setRowCount(0)
        if df is None or df.empty:
            return
        for _, row in df.iterrows():
            r = table.rowCount()
            table.insertRow(r)
            date_str = self._fmt_date(row.get("transaction_date"))
            desc = str(row.get("description", ""))
            amt = float(row.get("amount", 0.0) or 0.0)
            facct = str(row.get("from_account", ""))
            cat = str(row.get("category", ""))
            subc = str(row.get("sub_category", ""))
            cat_sub = f"{cat}/{subc}" if cat or subc else ""

            it0 = QtWidgets.QTableWidgetItem(date_str)
            it1 = QtWidgets.QTableWidgetItem(desc)
            it2 = QtWidgets.QTableWidgetItem(self._fmt_currency(amt))
            it3 = QtWidgets.QTableWidgetItem(facct)
            it4 = QtWidgets.QTableWidgetItem(cat_sub)
            it2.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            table.setItem(r, 0, it0)
            table.setItem(r, 1, it1)
            table.setItem(r, 2, it2)
            table.setItem(r, 3, it3)
            table.setItem(r, 4, it4)

        table.resizeColumnsToContents()
        table.setSortingEnabled(True)

    @staticmethod
    def _fmt_currency(value: float) -> str:
        try:
            return f"${value:,.2f}"
        except Exception:  # pragma: no cover
            return str(value)

    @staticmethod
    def _fmt_date(value) -> str:
        try:
            return str(getattr(value, "date", lambda: value)()) if hasattr(value, "date") else str(value)[:10]
        except Exception:  # pragma: no cover
            return str(value)[:10]
