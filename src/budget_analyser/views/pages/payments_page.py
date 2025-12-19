from __future__ import annotations

import logging
from typing import List

from PySide6 import QtCore, QtWidgets

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.controller import PaymentsReconciliationController


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
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # Header: Title + Month combobox
        header_row = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Payments Reconciliation")
        tf = title.font()
        tf.setPointSize(16)
        tf.setBold(True)
        title.setFont(tf)
        header_row.addWidget(title)
        header_row.addStretch(1)
        header_row.addWidget(QtWidgets.QLabel("Month:"))
        self.month_combo = QtWidgets.QComboBox()
        header_row.addWidget(self.month_combo)
        root.addLayout(header_row)

        # Tables row: left = Payments Made, right = Payment Confirmations
        tables_row = QtWidgets.QHBoxLayout()

        # Left panel
        left_panel = QtWidgets.QVBoxLayout()
        left_header = QtWidgets.QHBoxLayout()
        left_header.addWidget(QtWidgets.QLabel("Payments Made"))
        left_header.addStretch(1)
        self.left_count = QtWidgets.QLabel("0 items")
        self.left_total = QtWidgets.QLabel("$0.00")
        left_header.addWidget(self.left_count)
        left_header.addSpacing(8)
        left_header.addWidget(self.left_total)
        left_panel.addLayout(left_header)
        self.table_left = QtWidgets.QTableWidget(0, 5)
        self.table_left.setHorizontalHeaderLabels([
            "Date",
            "Description",
            "Amount",
            "From Account",
            "Category/Sub",
        ])
        self._prep_table(self.table_left)
        left_panel.addWidget(self.table_left)

        # Right panel
        right_panel = QtWidgets.QVBoxLayout()
        right_header = QtWidgets.QHBoxLayout()
        right_header.addWidget(QtWidgets.QLabel("Payment Confirmations"))
        right_header.addStretch(1)
        self.right_count = QtWidgets.QLabel("0 items")
        self.right_total = QtWidgets.QLabel("$0.00")
        right_header.addWidget(self.right_count)
        right_header.addSpacing(8)
        right_header.addWidget(self.right_total)
        right_panel.addLayout(right_header)
        self.table_right = QtWidgets.QTableWidget(0, 5)
        self.table_right.setHorizontalHeaderLabels([
            "Date",
            "Description",
            "Amount",
            "From Account",
            "Category/Sub",
        ])
        self._prep_table(self.table_right)
        right_panel.addWidget(self.table_right)

        # Add to row with equal stretch
        left_container = QtWidgets.QWidget()
        left_container.setObjectName("card")
        left_container.setLayout(QtWidgets.QVBoxLayout())
        left_container.layout().setContentsMargins(12, 12, 12, 12)
        left_container.layout().addLayout(left_panel)

        right_container = QtWidgets.QWidget()
        right_container.setObjectName("card")
        right_container.setLayout(QtWidgets.QVBoxLayout())
        right_container.layout().setContentsMargins(12, 12, 12, 12)
        right_container.layout().addLayout(right_panel)

        tables_row.addWidget(left_container, 1)
        tables_row.addWidget(right_container, 1)
        root.addLayout(tables_row)

        # Summary bar
        summary_card = QtWidgets.QWidget()
        summary_card.setObjectName("card")
        summary_layout = QtWidgets.QHBoxLayout(summary_card)
        summary_layout.setContentsMargins(12, 10, 12, 10)
        self.sum_label = QtWidgets.QLabel("Totals: Payments $0.00 | Confirmations $0.00 | Diff $0.00")
        summary_layout.addWidget(self.sum_label)
        summary_layout.addStretch(1)
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
        tbl.verticalHeader().setDefaultSectionSize(26)

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
