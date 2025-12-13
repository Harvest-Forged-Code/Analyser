from __future__ import annotations

import logging
from typing import List

from PySide6 import QtWidgets

from budget_analyser.presentation.controllers import MonthlyReports


class EarningsPage(QtWidgets.QWidget):
    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        super().__init__()
        self._reports = reports
        self._logger = logger
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header = QtWidgets.QLabel("Earnings")
        f = header.font()
        f.setPointSize(16)
        f.setBold(True)
        header.setFont(f)
        layout.addWidget(header)

        view = QtWidgets.QTextEdit(readOnly=True)
        view.setText(self._build_text())
        layout.addWidget(view)

    def _build_text(self) -> str:
        if not self._reports:
            return "No earnings to display."
        lines: list[str] = ["Earnings overview by month:"]
        for mr in self._reports:
            lines.append("")
            lines.append(f"Month: {mr.month}")
            lines.append(str(mr.earnings.head(10)))
        return "\n".join(lines)
