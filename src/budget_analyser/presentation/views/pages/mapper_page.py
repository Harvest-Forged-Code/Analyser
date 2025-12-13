from __future__ import annotations

import logging
from PySide6 import QtWidgets, QtCore


class MapperPage(QtWidgets.QWidget):
    def __init__(self, logger: logging.Logger):
        super().__init__()
        self._logger = logger
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        header = QtWidgets.QLabel("Mapper")
        f = header.font()
        f.setPointSize(16)
        f.setBold(True)
        header.setFont(f)
        layout.addWidget(header)

        placeholder = QtWidgets.QLabel("Mapper - coming soon")
        placeholder.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        layout.addWidget(placeholder)
