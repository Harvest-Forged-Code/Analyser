from __future__ import annotations

import logging
from pathlib import Path

from PySide6 import QtWidgets, QtCore, QtGui

from budget_analyser.controller import UploadController


class UploadPage(QtWidgets.QWidget):
    """Page for uploading bank statement CSV files."""

    # Signal emitted when a statement is successfully uploaded
    upload_successful = QtCore.Signal()

    def __init__(self, logger: logging.Logger, controller: UploadController):
        super().__init__()
        self._logger = logger
        self._controller = controller
        self._selected_file: Path | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        # Main scroll area to handle overflow
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        container = QtWidgets.QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Header section with icon
        header_container = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        icon_label = QtWidgets.QLabel("⬆️")
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)

        title_container = QtWidgets.QWidget()
        title_layout = QtWidgets.QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        header = QtWidgets.QLabel("Upload Statement")
        header.setObjectName("pageTitle")
        f = header.font()
        f.setPointSize(24)
        f.setBold(True)
        header.setFont(f)
        title_layout.addWidget(header)

        subtitle = QtWidgets.QLabel(
            "Upload your bank statement CSV file and it will be validated against the expected format"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 13px; color: #A78BFA;")
        title_layout.addWidget(subtitle)

        header_layout.addWidget(title_container, 1)
        layout.addWidget(header_container)

        # Form container with modern card design
        form_container = QtWidgets.QWidget()
        form_container.setObjectName("uploadFormCard")
        form_container.setStyleSheet("""
            QWidget#uploadFormCard {
                background: rgba(18, 18, 20, 0.95);
                border: 1px solid rgba(60, 60, 70, 0.3);
                border-radius: 18px;
                padding: 24px;
            }
        """)
        form_layout = QtWidgets.QVBoxLayout(form_container)
        form_layout.setContentsMargins(24, 24, 24, 24)
        form_layout.setSpacing(20)

        # Section title
        section_title = QtWidgets.QLabel("STATEMENT DETAILS")
        section_title.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            color: #8B5CF6;
            margin-bottom: 8px;
        """)
        form_layout.addWidget(section_title)

        # Account Type field
        account_type_container = self._create_field_container()
        account_type_layout = account_type_container.layout()

        account_type_label = self._create_field_label("Account Type")
        account_type_layout.addWidget(account_type_label)

        self._account_type_combo = QtWidgets.QComboBox()
        self._account_type_combo.addItems(["Credit Card", "Checking/Debit Account"])
        self._account_type_combo.setMinimumHeight(44)
        self._account_type_combo.currentIndexChanged.connect(self._on_account_type_changed)
        account_type_layout.addWidget(self._account_type_combo)

        form_layout.addWidget(account_type_container)

        # Bank/Account field
        bank_container = self._create_field_container()
        bank_layout = bank_container.layout()

        bank_label = self._create_field_label("Bank / Account")
        bank_layout.addWidget(bank_label)

        self._bank_combo = QtWidgets.QComboBox()
        self._bank_combo.setMinimumHeight(44)
        bank_layout.addWidget(self._bank_combo)

        form_layout.addWidget(bank_container)

        # File selection field
        file_container = self._create_field_container()
        file_layout = file_container.layout()

        file_label = self._create_field_label("CSV File")
        file_layout.addWidget(file_label)

        file_input_container = QtWidgets.QWidget()
        file_input_layout = QtWidgets.QHBoxLayout(file_input_container)
        file_input_layout.setContentsMargins(0, 0, 0, 0)
        file_input_layout.setSpacing(12)

        self._file_label = QtWidgets.QLineEdit()
        self._file_label.setReadOnly(True)
        self._file_label.setPlaceholderText("No file selected")
        self._file_label.setMinimumHeight(44)
        file_input_layout.addWidget(self._file_label, 1)

        self._browse_btn = QtWidgets.QPushButton("Browse...")
        self._browse_btn.setObjectName("secondaryButton")
        self._browse_btn.setMinimumHeight(44)
        self._browse_btn.setMinimumWidth(120)
        self._browse_btn.setStyleSheet("""
            QPushButton#secondaryButton {
                background: rgba(139, 92, 246, 0.15);
                border: 1px solid rgba(168, 85, 247, 0.3);
                color: #DDD6FE;
            }
            QPushButton#secondaryButton:hover {
                background: rgba(139, 92, 246, 0.25);
                border-color: rgba(168, 85, 247, 0.5);
            }
        """)
        self._browse_btn.clicked.connect(self._browse_file)
        file_input_layout.addWidget(self._browse_btn)

        file_layout.addWidget(file_input_container)
        form_layout.addWidget(file_container)

        layout.addWidget(form_container)

        # Action buttons
        btn_container = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(12)

        self._validate_btn = QtWidgets.QPushButton("Validate File")
        self._validate_btn.setObjectName("actionButton")
        self._validate_btn.setMinimumHeight(48)
        self._validate_btn.setMinimumWidth(140)
        self._validate_btn.setStyleSheet("""
            QPushButton#actionButton {
                background: rgba(139, 92, 246, 0.2);
                border: 1px solid rgba(168, 85, 247, 0.4);
                color: #E9D5FF;
                font-weight: 600;
            }
            QPushButton#actionButton:hover {
                background: rgba(139, 92, 246, 0.3);
                border-color: rgba(168, 85, 247, 0.6);
            }
        """)
        self._validate_btn.clicked.connect(self._validate_file)
        btn_layout.addWidget(self._validate_btn)

        self._upload_btn = QtWidgets.QPushButton("Upload Statement")
        self._upload_btn.setMinimumHeight(48)
        self._upload_btn.setMinimumWidth(160)
        self._upload_btn.clicked.connect(self._upload_file)
        btn_layout.addWidget(self._upload_btn)

        btn_layout.addStretch(1)

        self._clear_btn = QtWidgets.QPushButton("Clear Form")
        self._clear_btn.setObjectName("clearButton")
        self._clear_btn.setMinimumHeight(48)
        self._clear_btn.setMinimumWidth(120)
        self._clear_btn.setStyleSheet("""
            QPushButton#clearButton {
                background: transparent;
                border: 1px solid rgba(168, 85, 247, 0.2);
                color: #A78BFA;
                font-weight: 600;
            }
            QPushButton#clearButton:hover {
                background: rgba(139, 92, 246, 0.1);
                border-color: rgba(168, 85, 247, 0.3);
            }
        """)
        self._clear_btn.clicked.connect(self._clear_form)
        btn_layout.addWidget(self._clear_btn)

        layout.addWidget(btn_container)

        # Message frame
        self._message_frame = QtWidgets.QFrame()
        self._message_frame.setVisible(False)
        self._message_frame.setStyleSheet("""
            QFrame {
                border-radius: 14px;
                padding: 16px;
            }
        """)
        msg_layout = QtWidgets.QHBoxLayout(self._message_frame)
        msg_layout.setContentsMargins(20, 16, 20, 16)
        msg_layout.setSpacing(12)

        self._message_icon = QtWidgets.QLabel()
        self._message_icon.setFixedSize(28, 28)
        self._message_icon.setStyleSheet("font-size: 20px;")
        msg_layout.addWidget(self._message_icon)

        self._message_label = QtWidgets.QLabel()
        self._message_label.setWordWrap(True)
        self._message_label.setStyleSheet("font-size: 13px; line-height: 1.5;")
        msg_layout.addWidget(self._message_label, 1)

        layout.addWidget(self._message_frame)

        # Info cards grid
        info_grid = QtWidgets.QWidget()
        info_layout = QtWidgets.QGridLayout(info_grid)
        info_layout.setSpacing(16)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Expected Format card
        format_card = self._create_info_card("Expected Format", "format_icon")
        format_card_layout = format_card.layout()

        self._format_info = QtWidgets.QLabel("Select a bank to see expected columns")
        self._format_info.setWordWrap(True)
        self._format_info.setStyleSheet("""
            font-size: 12px;
            color: #C4B5FD;
            line-height: 1.6;
        """)
        format_card_layout.addWidget(self._format_info)

        info_layout.addWidget(format_card, 0, 0)

        # Upload Status card
        status_card = self._create_info_card("Upload Status", "status_icon")
        status_card_layout = status_card.layout()

        self._status_container = QtWidgets.QWidget()
        self._status_layout = QtWidgets.QGridLayout(self._status_container)
        self._status_layout.setContentsMargins(0, 8, 0, 0)
        self._status_layout.setSpacing(12)
        status_card_layout.addWidget(self._status_container)

        # Store status labels for updates
        self._status_labels: dict[str, QtWidgets.QLabel] = {}

        info_layout.addWidget(status_card, 0, 1)

        layout.addWidget(info_grid)

        layout.addStretch(1)

        # Initialize
        self._on_account_type_changed()
        self._bank_combo.currentIndexChanged.connect(self._update_format_info)
        self._refresh_upload_status()

    def _create_field_container(self) -> QtWidgets.QWidget:
        """Create a container widget for form fields with consistent styling."""
        container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)
        return container

    def _create_field_label(self, text: str) -> QtWidgets.QLabel:
        """Create a consistently styled field label."""
        label = QtWidgets.QLabel(text)
        label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #DDD6FE;
            letter-spacing: 0.3px;
        """)
        return label

    def _create_info_card(self, title: str, icon_name: str) -> QtWidgets.QWidget:
        """Create an info card with consistent styling."""
        card = QtWidgets.QWidget()
        card.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 16, 51, 0.5), stop:1 rgba(20, 12, 36, 0.3));
                border: 1px solid rgba(168, 85, 247, 0.12);
                border-radius: 16px;
            }
        """)

        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(12)

        # Card header
        header_container = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        icon_map = {
            "format_icon": "📄",
            "status_icon": "✓",
        }
        icon = QtWidgets.QLabel(icon_map.get(icon_name, "ℹ️"))
        icon.setStyleSheet("font-size: 18px;")
        header_layout.addWidget(icon)

        title_label = QtWidgets.QLabel(title.upper())
        title_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            color: #8B5CF6;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)

        card_layout.addWidget(header_container)

        return card

    def _refresh_upload_status(self) -> None:
        """Refresh the upload status display showing all banks with checkmarks."""
        # Clear existing widgets
        while self._status_layout.count():
            item = self._status_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._status_labels.clear()

        # Get status for all banks
        status_list = self._controller.get_bank_upload_status()

        if not status_list:
            no_banks_label = QtWidgets.QLabel("No banks configured")
            no_banks_label.setStyleSheet("color: #6B7280; font-size: 12px;")
            self._status_layout.addWidget(no_banks_label, 0, 0)
            return

        # Add column headers
        credit_header = QtWidgets.QLabel("CREDIT CARDS")
        credit_header.setStyleSheet("""
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            color: #8B5CF6;
        """)
        debit_header = QtWidgets.QLabel("CHECKING ACCOUNTS")
        debit_header.setStyleSheet("""
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            color: #8B5CF6;
        """)
        self._status_layout.addWidget(credit_header, 0, 0)
        self._status_layout.addWidget(debit_header, 0, 1)

        # Separate by account type
        credit_banks = [(b, u) for b, t, u in status_list if t == "credit"]
        debit_banks = [(b, u) for b, t, u in status_list if t == "debit"]

        # Add credit card statuses
        for row, (bank, is_uploaded) in enumerate(credit_banks, start=1):
            label = self._create_status_label(bank, is_uploaded)
            self._status_layout.addWidget(label, row, 0)
            self._status_labels[f"credit_{bank}"] = label

        # Add debit account statuses
        for row, (bank, is_uploaded) in enumerate(debit_banks, start=1):
            label = self._create_status_label(bank, is_uploaded)
            self._status_layout.addWidget(label, row, 1)
            self._status_labels[f"debit_{bank}"] = label

    def _create_status_label(self, bank: str, is_uploaded: bool) -> QtWidgets.QLabel:
        """Create a status label for a bank with checkmark or X."""
        bank_display = bank.replace("_", " ").title()
        if is_uploaded:
            icon = "✓"
            color = "#10B981"
        else:
            icon = "○"
            color = "#6B7280"

        label = QtWidgets.QLabel(f"{icon}  {bank_display}")
        label.setStyleSheet(f"""
            color: {color};
            font-size: 12px;
            font-weight: 500;
            padding: 4px 0;
        """)
        return label

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
            self._format_info.setText("Select a bank to see expected columns")
            return

        columns = self._controller.get_expected_columns(bank_id)
        if columns:
            columns_html = ", ".join([f"<b>{col}</b>" for col in columns])
            self._format_info.setText(
                f"<span style='color: #E9D5FF;'>{bank_id.replace('_', ' ').title()}:</span><br>"
                f"<span style='color: #C4B5FD;'>{columns_html}</span>"
            )
        else:
            self._format_info.setText(
                f"No column mapping configured for {bank_id.replace('_', ' ').title()}"
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
            self._show_message("Please select a CSV file first", is_error=True)
            return

        bank_id = self._get_selected_bank_id()
        if not bank_id:
            self._show_message("Please select a valid bank/account", is_error=True)
            return

        is_valid, message, _ = self._controller.validate_csv(self._selected_file, bank_id)

        if is_valid:
            self._show_message(
                f"{message}\n\nThe file is ready to upload",
                is_error=False
            )
        else:
            self._show_message(f"Validation failed: {message}", is_error=True)

    def _upload_file(self) -> None:
        if not self._selected_file:
            self._show_message("Please select a CSV file first", is_error=True)
            return

        bank_id = self._get_selected_bank_id()
        if not bank_id:
            self._show_message("Please select a valid bank/account", is_error=True)
            return

        account_type = "credit" if self._account_type_combo.currentIndex() == 0 else "debit"

        result = self._controller.upload_statement(
            self._selected_file, bank_id, account_type
        )

        if result.success:
            self._show_message(f"{result.message}", is_error=False)
            self._clear_form()
            self._refresh_upload_status()
            self.upload_successful.emit()
        else:
            self._show_message(f"Upload failed: {result.message}", is_error=True)

    def _clear_form(self) -> None:
        self._selected_file = None
        self._file_label.clear()
        self._hide_message()

    def _show_message(self, message: str, is_error: bool) -> None:
        self._message_frame.setVisible(True)
        self._message_label.setText(message)

        if is_error:
            self._message_frame.setStyleSheet("""
                QFrame {
                    background: rgba(239, 68, 68, 0.1);
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 14px;
                }
            """)
            self._message_label.setStyleSheet("color: #FCA5A5; font-size: 13px;")
            self._message_icon.setText("⚠️")
        else:
            self._message_frame.setStyleSheet("""
                QFrame {
                    background: rgba(16, 185, 129, 0.1);
                    border: 1px solid rgba(16, 185, 129, 0.3);
                    border-radius: 14px;
                }
            """)
            self._message_label.setStyleSheet("color: #6EE7B7; font-size: 13px;")
            self._message_icon.setText("✓")

    def _hide_message(self) -> None:
        self._message_frame.setVisible(False)
