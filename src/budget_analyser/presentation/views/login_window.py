"""Login window (PySide6).

Single responsibility:
    Presents a fullscreen login UI and emits a signal on successful login.

Notes:
    - Accepts password "123456" only (per requirement).
    - Emits `login_successful` Qt signal when auth passes.
"""

from __future__ import annotations

import logging
from PySide6 import QtCore, QtWidgets
from typing import Callable


class LoginWindow(QtWidgets.QWidget):
    login_successful = QtCore.Signal()

    def __init__(self, logger: logging.Logger, verify_password: Callable[[str], bool] | None = None):
        super().__init__()
        self._logger = logger
        # Injected password verification strategy (defaults to static 123456 check)
        self._verify_password = verify_password or (lambda s: s == "123456")
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Budget Analyser - Login")
        self.setObjectName("loginWindow")

        # Global modern style (dark theme with accent color and rounded elements)
        self.setStyleSheet(
            """
            #loginWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #0F172A, stop:1 #0B1220);
                color: #E6EDF3;
                font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
                font-size: 14px;
            }

            /* Card container */
            #card {
                background-color: rgba(22, 27, 34, 0.88);
                border: 1px solid rgba(240, 246, 252, 0.08);
                border-radius: 16px;
            }

            /* Typography */
            QLabel#title {
                font-size: 28px;
                font-weight: 600;
                letter-spacing: 0.3px;
                color: #F0F6FC;
            }
            QLabel#subtitle {
                color: #9DA7B1;
                font-size: 13px;
            }

            /* Inputs */
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(240, 246, 252, 0.12);
                border-radius: 10px;
                padding: 10px 12px;
                color: #E6EDF3;
                selection-background-color: #2D81FF;
            }
            QLineEdit:focus {
                border: 1px solid #2D81FF;
            }

            /* Buttons */
            QPushButton {
                background-color: #2D81FF;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                font-weight: 600;
                min-width: 120px;
            }
            QPushButton:hover { background-color: #3B8BFF; }
            QPushButton:pressed { background-color: #1F66E5; }
            QPushButton:disabled {
                background-color: #2f3545;
                color: #98A1B2;
            }
            """
        )

        # Root layout with vertical centering
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.addStretch(2)

        # Center row to horizontally center the card
        center_row = QtWidgets.QHBoxLayout()
        center_row.addStretch(1)

        # Card widget holding login controls
        card = QtWidgets.QWidget()
        card.setObjectName("card")
        card.setMinimumWidth(420)
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(14)

        title = QtWidgets.QLabel("Budget Analyser")
        title.setObjectName("title")
        title.setAlignment(QtCore.Qt.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QtWidgets.QLabel("Secure sign in")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        card_layout.addWidget(subtitle)

        # Spacer between heading and input
        card_layout.addSpacing(8)

        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter your password")
        self.password_edit.returnPressed.connect(self._on_login_clicked)
        card_layout.addWidget(self.password_edit)

        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.clicked.connect(self._on_login_clicked)
        self.login_button.setDefault(True)

        # Button row centered
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self.login_button)
        btn_row.addStretch(1)
        card_layout.addLayout(btn_row)

        # Subtle shadow for the card
        shadow = QtWidgets.QGraphicsDropShadowEffect(blurRadius=32, xOffset=0, yOffset=12)
        # Slightly transparent black shadow
        shadow.setColor(QtCore.Qt.black)
        card.setGraphicsEffect(shadow)

        center_row.addWidget(card)
        center_row.addStretch(1)
        root.addLayout(center_row)

        root.addStretch(3)

        # Fullscreen view
        self.setWindowState(QtCore.Qt.WindowFullScreen)

    def _on_login_clicked(self) -> None:
        entered = self.password_edit.text()
        if self._verify_password(entered):
            self._logger.info("Login successful")
            self.login_successful.emit()
        else:
            self._logger.warning("Login failed")
            QtWidgets.QMessageBox.warning(self, "Login Failed", "Incorrect password.")
