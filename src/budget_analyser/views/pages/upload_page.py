from __future__ import annotations

import logging
from pathlib import Path

from PySide6 import QtWidgets, QtCore, QtGui

from budget_analyser.controller import UploadController


class UploadPage(QtWidgets.QWidget):
    def __init__(self, logger: logging.Logger, controller: UploadController):
        super().__init__()
        self._logger = logger
        self._controller = controller
        self._selected_file: Path | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QtWidgets.QLabel("Upload Statement")
        f = header.font()
        f.setPointSize(18)
        f.setBold(True)
        header.setFont(f)
        layout.addWidget(header)

        subtitle = QtWidgets.QLabel(
            "Upload your bank statement CSV file. The file will be validated "
            "against the expected format before being saved."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #888; margin-bottom: 8px;")
        layout.addWidget(subtitle)

        form_group = QtWidgets.QGroupBox("Statement Details")
        form_layout = QtWidgets.QFormLayout(form_group)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(16, 20, 16, 16)

        self._account_type_combo = QtWidgets.QComboBox()
        self._account_type_combo.addItems(["Credit Card", "Checking/Debit Account"])
        self._account_type_combo.currentIndexChanged.connect(self._on_account_type_changed)
        form_layout.addRow("Account Type:", self._account_type_combo)

        self._bank_combo = QtWidgets.QComboBox()
        self._bank_combo.setMinimumWidth(200)
        form_layout.addRow("Bank/Account:", self._bank_combo)

        file_widget = QtWidgets.QWidget()
        file_layout = QtWidgets.QHBoxLayout(file_widget)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(8)

        self._file_label = QtWidgets.QLineEdit()
        self._file_label.setReadOnly(True)
        self._file_label.setPlaceholderText("No file selected")
        file_layout.addWidget(self._file_label, 1)

        self._browse_btn = QtWidgets.QPushButton("Browse...")
        self._browse_btn.setFixedWidth(100)
        self._browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(self._browse_btn)

        form_layout.addRow("CSV File:", file_widget)

        layout.addWidget(form_group)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(12)

        self._validate_btn = QtWidgets.QPushButton("Validate")
        self._validate_btn.setFixedWidth(120)
        self._validate_btn.clicked.connect(self._validate_file)
        btn_layout.addWidget(self._validate_btn)

        self._upload_btn = QtWidgets.QPushButton("Upload")
        self._upload_btn.setFixedWidth(120)
        self._upload_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )
        self._upload_btn.clicked.connect(self._upload_file)
        btn_layout.addWidget(self._upload_btn)

        btn_layout.addStretch(1)

        self._clear_btn = QtWidgets.QPushButton("Clear")
        self._clear_btn.setFixedWidth(100)
        self._clear_btn.clicked.connect(self._clear_form)
        btn_layout.addWidget(self._clear_btn)

        layout.addLayout(btn_layout)

        self._message_frame = QtWidgets.QFrame()
        self._message_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._message_frame.setVisible(False)
        msg_layout = QtWidgets.QHBoxLayout(self._message_frame)
        msg_layout.setContentsMargins(12, 12, 12, 12)

        self._message_icon = QtWidgets.QLabel()
        self._message_icon.setFixedSize(24, 24)
        msg_layout.addWidget(self._message_icon)

        self._message_label = QtWidgets.QLabel()
        self._message_label.setWordWrap(True)
        msg_layout.addWidget(self._message_label, 1)

        layout.addWidget(self._message_frame)

        info_group = QtWidgets.QGroupBox("Expected Format")
        info_layout = QtWidgets.QVBoxLayout(info_group)
        info_layout.setContentsMargins(16, 16, 16, 16)

        self._format_info = QtWidgets.QLabel("Select a bank to see expected columns.")
        self._format_info.setWordWrap(True)
        self._format_info.setStyleSheet("color: #666;")
        info_layout.addWidget(self._format_info)

        layout.addWidget(info_group)

        layout.addStretch(1)

        self._on_account_type_changed()
        self._bank_combo.currentIndexChanged.connect(self._update_format_info)

    def _on_account_type_changed(self) -> None:
        account_type = "credit" if self._account_type_combo.currentIndex() == 0 else "debit"
        banks = self._controller.get_available_banks(account_type)

        self._bank_combo.clear()
        if banks:
            self._bank_combo.addItems([b.replace("_", " ").title() for b in banks])
            self._bank_combo.setProperty("bank_ids", banks)
        else:
            self._bank_combo.addItem("No accounts configured")
            self._bank_combo.setProperty("bank_ids", [])

        self._update_format_info()

    def _get_selected_bank_id(self) -> str | None:
        bank_ids = self._bank_combo.property("bank_ids") or []
        idx = self._bank_combo.currentIndex()
        if 0 <= idx < len(bank_ids):
            return bank_ids[idx]
        return None

    def _update_format_info(self) -> None:
        bank_id = self._get_selected_bank_id()
        if not bank_id:
            self._format_info.setText("Select a bank to see expected columns.")
            return

        columns = self._controller.get_expected_columns(bank_id)
        if columns:
            self._format_info.setText(
                f"<b>Expected columns for {bank_id.replace('_', ' ').title()}:</b><br>"
                f"{', '.join(columns)}"
            )
        else:
            self._format_info.setText(
                f"No column mapping configured for {bank_id.replace('_', ' ').title()}."
            )

    def _browse_file(self) -> None:
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Bank Statement CSV",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        if file_path:
            self._selected_file = Path(file_path)
            self._file_label.setText(file_path)
            self._hide_message()

    def _validate_file(self) -> None:
        if not self._selected_file:
            self._show_message("Please select a CSV file first.", is_error=True)
            return

        bank_id = self._get_selected_bank_id()
        if not bank_id:
            self._show_message("Please select a valid bank/account.", is_error=True)
            return

        is_valid, message, _ = self._controller.validate_csv(self._selected_file, bank_id)

        if is_valid:
            self._show_message(
                f"✓ {message}\n\nThe file is ready to upload.",
                is_error=False
            )
        else:
            self._show_message(f"✗ Validation failed:\n{message}", is_error=True)

    def _upload_file(self) -> None:
        if not self._selected_file:
            self._show_message("Please select a CSV file first.", is_error=True)
            return

        bank_id = self._get_selected_bank_id()
        if not bank_id:
            self._show_message("Please select a valid bank/account.", is_error=True)
            return

        account_type = "credit" if self._account_type_combo.currentIndex() == 0 else "debit"

        result = self._controller.upload_statement(
            self._selected_file, bank_id, account_type
        )

        if result.success:
            self._show_message(f"✓ {result.message}", is_error=False)
            self._clear_form()
        else:
            self._show_message(f"✗ Upload failed:\n{result.message}", is_error=True)

    def _clear_form(self) -> None:
        self._selected_file = None
        self._file_label.clear()
        self._hide_message()

    def _show_message(self, message: str, is_error: bool) -> None:
        self._message_frame.setVisible(True)
        self._message_label.setText(message)

        if is_error:
            self._message_frame.setStyleSheet(
                "QFrame { background-color: #ffebee; border: 1px solid #ef5350; "
                "border-radius: 4px; }"
            )
            self._message_label.setStyleSheet("color: #c62828;")
            self._message_icon.setText("⚠")
            self._message_icon.setStyleSheet("color: #c62828; font-size: 18px;")
        else:
            self._message_frame.setStyleSheet(
                "QFrame { background-color: #e8f5e9; border: 1px solid #66bb6a; "
                "border-radius: 4px; }"
            )
            self._message_label.setStyleSheet("color: #2e7d32;")
            self._message_icon.setText("✓")
            self._message_icon.setStyleSheet("color: #2e7d32; font-size: 18px;")

    def _hide_message(self) -> None:
        self._message_frame.setVisible(False)
