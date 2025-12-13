"""Dashboard window (PySide6).

Single responsibility:
    Display report summaries provided by the backend controller.
"""

from __future__ import annotations

import logging
from typing import List
from PySide6 import QtWidgets

from budget_analyser.presentation.controllers import MonthlyReports


class DashboardWindow(QtWidgets.QMainWindow):
    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        super().__init__()
        self._reports = reports
        self._logger = logger
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Budget Analyser - Dashboard")
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        header = QtWidgets.QLabel("Reports Dashboard")
        f = header.font()
        f.setPointSize(18)
        f.setBold(True)
        header.setFont(f)
        layout.addWidget(header)

        info = QtWidgets.QTextEdit()
        info.setReadOnly(True)
        info.setMinimumSize(800, 400)

        if not self._reports:
            info.setText("No reports available. Make sure statements data is present.")
        else:
            lines: list[str] = []
            for mr in self._reports:
                lines.append(f"Month: {mr.month}")
                # Render simple summaries; tables can be large, so show heads
                lines.append("- Earnings (top):")
                lines.append(str(mr.earnings.head()))
                lines.append("- Expenses (top):")
                lines.append(str(mr.expenses.head()))
                lines.append("")
            info.setText("\n".join(lines))

        layout.addWidget(info)
