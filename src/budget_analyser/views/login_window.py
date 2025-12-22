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

from budget_analyser.version import get_version, APP_NAME


class LoginWindow(QtWidgets.QWidget):
    login_successful = QtCore.Signal()
    theme_toggle_requested = QtCore.Signal()

    def __init__(
        self,
        logger: logging.Logger,
        verify_password: Callable[[str], bool] | None = None,
        current_theme: str = "dark",
    ):
        super().__init__()
        self._logger = logger
        # Injected password verification strategy (defaults to static 123456 check)
        self._verify_password = verify_password or (lambda s: s == "123456")
        self._current_theme = current_theme.lower()
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle(f"{APP_NAME} v{get_version()} - Login")
        self.setObjectName("loginWindow")

        # Styling is provided by the application stylesheet (supports light/dark themes).
        # Apply an additional, login-only stylesheet to keep the input/button look
        # scoped to this window, and enlarge the title per request.
        self.setStyleSheet(self._login_stylesheet())

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

        # Top controls row (theme toggle on the right)
        top_controls = QtWidgets.QHBoxLayout()
        top_controls.addStretch(1)
        self.theme_btn = QtWidgets.QPushButton()
        self.theme_btn.setObjectName("themeToggle")
        self.set_theme_indicator(self._current_theme)
        self.theme_btn.clicked.connect(self.theme_toggle_requested.emit)
        top_controls.addWidget(self.theme_btn, alignment=QtCore.Qt.AlignRight)
        card_layout.addLayout(top_controls)

        title = QtWidgets.QLabel(f"{APP_NAME} v{get_version()}")
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

    def _login_stylesheet(self, theme: str | None = None) -> str:
        """Return QSS scoped only to the login window.

        Notes:
            - Increases the title size so it doesn't look small.
            - Styles inputs and buttons similar to the provided snippet.
            - Scoped with QWidget#loginWindow to avoid affecting other windows.
        """
        t = (theme or self._current_theme or "dark").lower()
        if t == "light":
            title_color = "#1F2328"
            subtitle_color = "#57606A"
            line_bg = "#FFFFFF"
            line_border = "#D0D7DE"
            line_text = "#1F2328"
        else:
            title_color = "#F0F6FC"
            subtitle_color = "#9DA7B1"
            line_bg = "rgba(255, 255, 255, 0.06)"
            line_border = "rgba(240, 246, 252, 0.12)"
            line_text = "#E6EDF3"

        return f"""
            /* Typography */
            QWidget#loginWindow QLabel#title {{
                font-size: 36px;               /* enlarged from 28px */
                font-weight: 600;
                letter-spacing: 0.3px;
                color: {title_color};
            }}
            QWidget#loginWindow QLabel#subtitle {{
                color: {subtitle_color};
                font-size: 13px;
            }}

            /* Inputs */
            QWidget#loginWindow QLineEdit {{
                background-color: {line_bg};
                border: 1px solid {line_border};
                border-radius: 10px;
                padding: 10px 12px;
                color: {line_text};
                selection-background-color: #2D81FF;
            }}
            QWidget#loginWindow QLineEdit:focus {{
                border: 1px solid #2D81FF;
            }}

            /* Buttons */
            QWidget#loginWindow QPushButton {{
                background-color: #2D81FF;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                font-weight: 600;
                min-width: 120px;
            }}
            QWidget#loginWindow QPushButton:hover {{ background-color: #3B8BFF; }}
            QWidget#loginWindow QPushButton:pressed {{ background-color: #1F66E5; }}
            QWidget#loginWindow QPushButton:disabled {{
                background-color: #2f3545;
                color: #98A1B2;
            }}

            /* Make the theme toggle button transparent (override generic QPushButton rule) */
            QWidget#loginWindow QPushButton#themeToggle {{
                background: transparent;
                color: inherit;
                border: none;
                padding: 6px; /* compact */
                min-width: 0px;
            }}
            QWidget#loginWindow QPushButton#themeToggle:hover {{
                background: rgba(0,0,0,0.06);
            }}
            QWidget#loginWindow QPushButton#themeToggle:pressed {{
                background: rgba(0,0,0,0.12);
            }}
        """

    def _on_login_clicked(self) -> None:
        entered = self.password_edit.text()
        if self._verify_password(entered):
            self._logger.info("Login successful")
            self.login_successful.emit()
        else:
            self._logger.warning("Login failed")
            QtWidgets.QMessageBox.warning(self, "Login Failed", "Incorrect password.")

    # External hook to update the theme toggle icon when theme changes elsewhere
    def set_theme_indicator(self, theme: str) -> None:
        t = theme.lower()
        # Show the icon for the theme you will switch to on click
        self.theme_btn.setText("☀️" if t == "dark" else "🌙")
        self._current_theme = t
        # Also re-apply the login stylesheet to ensure proper contrast on light/dark
        try:
            self.setStyleSheet(self._login_stylesheet(theme=t))
        except Exception:  # pragma: no cover - defensive
            pass
