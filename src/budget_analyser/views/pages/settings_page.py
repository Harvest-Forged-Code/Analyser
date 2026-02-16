from __future__ import annotations

import logging
from PySide6 import QtWidgets, QtCore

from budget_analyser.controller import SettingsController
from budget_analyser.views.pages._page_base import ModernPageMixin


class SettingsPage(QtWidgets.QWidget):
    def __init__(self, logger: logging.Logger, controller: SettingsController):
        super().__init__()
        self._logger = logger
        self._controller = controller
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

        # Page header
        page_header = ModernPageMixin.create_page_header(
            title="Settings",
            subtitle="Configure application preferences and security",
            icon="⚙️"
        )
        root.addWidget(page_header)

        # Logging settings card
        log_card, log_layout = ModernPageMixin.create_card("LOGGING")

        level_label = ModernPageMixin.create_control_label("Log Level")
        log_layout.addWidget(level_label)

        self.level_combo = QtWidgets.QComboBox()
        self.level_combo.addItems(self._controller.get_log_levels())
        # Preselect current level
        current = self._controller.get_current_log_level()
        idx = self.level_combo.findText(current, QtCore.Qt.MatchFlag.MatchFixedString)
        if idx >= 0:
            self.level_combo.setCurrentIndex(idx)
        ModernPageMixin.style_combo_box(self.level_combo)
        log_layout.addWidget(self.level_combo)

        self.apply_level_btn = ModernPageMixin.create_action_button("Apply Log Level", primary=True)
        self.apply_level_btn.clicked.connect(self._apply_log_level)
        log_layout.addWidget(self.apply_level_btn)

        root.addWidget(log_card)

        # Password settings card
        pass_card, pass_layout = ModernPageMixin.create_card("PASSWORD")

        current_label = ModernPageMixin.create_control_label("Current Password")
        pass_layout.addWidget(current_label)

        self.current_pass = QtWidgets.QLineEdit()
        self.current_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.current_pass.setPlaceholderText("Enter current password")
        self.current_pass.setMinimumHeight(34)
        pass_layout.addWidget(self.current_pass)

        new_label = ModernPageMixin.create_control_label("New Password")
        pass_layout.addWidget(new_label)

        self.new_pass = QtWidgets.QLineEdit()
        self.new_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.new_pass.setPlaceholderText("Enter new password")
        self.new_pass.setMinimumHeight(34)
        pass_layout.addWidget(self.new_pass)

        confirm_label = ModernPageMixin.create_control_label("Confirm Password")
        pass_layout.addWidget(confirm_label)

        self.confirm_pass = QtWidgets.QLineEdit()
        self.confirm_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirm_pass.setPlaceholderText("Re-enter new password")
        self.confirm_pass.setMinimumHeight(34)
        pass_layout.addWidget(self.confirm_pass)

        self.update_pass_btn = ModernPageMixin.create_action_button("Update Password", primary=True)
        self.update_pass_btn.clicked.connect(self._update_password)
        pass_layout.addWidget(self.update_pass_btn)

        root.addWidget(pass_card)

        root.addStretch(1)

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
