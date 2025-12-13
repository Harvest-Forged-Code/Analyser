from __future__ import annotations

import logging
from PySide6 import QtWidgets, QtCore

from budget_analyser.presentation.controller import SettingsController


class SettingsPage(QtWidgets.QWidget):
    def __init__(self, logger: logging.Logger, controller: SettingsController):
        super().__init__()
        self._logger = logger
        self._controller = controller
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QtWidgets.QLabel("Settings")
        f = header.font()
        f.setPointSize(16)
        f.setBold(True)
        header.setFont(f)
        layout.addWidget(header)

        # Log level group
        log_group = QtWidgets.QGroupBox("Logging")
        log_layout = QtWidgets.QFormLayout(log_group)
        self.level_combo = QtWidgets.QComboBox()
        self.level_combo.addItems(self._controller.get_log_levels())
        # Preselect current level
        current = self._controller.get_current_log_level()
        idx = self.level_combo.findText(current, QtCore.Qt.MatchFlag.MatchFixedString)
        if idx >= 0:
            self.level_combo.setCurrentIndex(idx)
        self.apply_level_btn = QtWidgets.QPushButton("Apply")
        self.apply_level_btn.clicked.connect(self._apply_log_level)
        log_layout.addRow("Level", self.level_combo)
        log_layout.addRow("", self.apply_level_btn)
        layout.addWidget(log_group)

        # Password group
        pass_group = QtWidgets.QGroupBox("Password")
        form = QtWidgets.QFormLayout(pass_group)
        self.current_pass = QtWidgets.QLineEdit()
        self.current_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.new_pass = QtWidgets.QLineEdit()
        self.new_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirm_pass = QtWidgets.QLineEdit()
        self.confirm_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.update_pass_btn = QtWidgets.QPushButton("Update Password")
        self.update_pass_btn.clicked.connect(self._update_password)
        form.addRow("Current", self.current_pass)
        form.addRow("New", self.new_pass)
        form.addRow("Confirm", self.confirm_pass)
        form.addRow("", self.update_pass_btn)
        layout.addWidget(pass_group)

        layout.addStretch(1)

    # ---- Actions ----
    def _apply_log_level(self) -> None:
        level = self.level_combo.currentText()
        try:
            self._controller.apply_log_level(level)
            QtWidgets.QMessageBox.information(self, "Logging", f"Log level set to {level}.")
        except Exception as exc:  # pragma: no cover - defensive
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to set log level: {exc}")

    def _update_password(self) -> None:
        cur = self.current_pass.text()
        new = self.new_pass.text()
        confirm = self.confirm_pass.text()
        try:
            self._controller.change_password(cur, new, confirm)
            self.current_pass.clear()
            self.new_pass.clear()
            self.confirm_pass.clear()
            QtWidgets.QMessageBox.information(self, "Password", "Password updated successfully.")
        except Exception as exc:  # pragma: no cover - defensive
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update password: {exc}")
