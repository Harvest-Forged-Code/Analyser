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
        root.setContentsMargins(48, 40, 48, 40)
        root.setSpacing(0)
        root.addStretch(2)

        # Center row to horizontally center the card
        center_row = QtWidgets.QHBoxLayout()
        center_row.addStretch(1)

        # Card widget holding login controls
        card = QtWidgets.QWidget()
        card.setObjectName("card")
        card.setMinimumWidth(420)
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(16)

        # Top controls row (theme toggle on the right)
        top_controls = QtWidgets.QHBoxLayout()
        top_controls.addStretch(1)
        self.theme_btn = QtWidgets.QPushButton()
        self.theme_btn.setObjectName("themeToggle")
        self.set_theme_indicator(self._current_theme)
        self.theme_btn.clicked.connect(self.theme_toggle_requested.emit)
        self.theme_btn.setCursor(QtCore.Qt.PointingHandCursor)
        top_controls.addWidget(self.theme_btn, alignment=QtCore.Qt.AlignRight)
        card_layout.addLayout(top_controls)

        badge = QtWidgets.QLabel("Budget Analyser")
        badge.setObjectName("badge")
        badge.setAlignment(QtCore.Qt.AlignCenter)
        card_layout.addWidget(badge)

        title = QtWidgets.QLabel(f"{APP_NAME} v{get_version()}")
        title.setObjectName("title")
        title.setAlignment(QtCore.Qt.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QtWidgets.QLabel("Secure sign in")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        card_layout.addWidget(subtitle)

        helper = QtWidgets.QLabel(
            "Enter your workspace passcode to access your financial insights."
        )
        helper.setObjectName("helperText")
        helper.setAlignment(QtCore.Qt.AlignCenter)
        helper.setWordWrap(True)
        card_layout.addWidget(helper)

        # Spacer between heading and input
        card_layout.addSpacing(10)

        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_edit.setPlaceholderText("Enter your password")
        self.password_edit.setClearButtonEnabled(True)
        self.password_edit.setMinimumHeight(44)
        self.password_edit.returnPressed.connect(self._on_login_clicked)
        card_layout.addWidget(self.password_edit)

        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.clicked.connect(self._on_login_clicked)
        self.login_button.setDefault(True)
        self.login_button.setMinimumHeight(44)
        self.login_button.setCursor(QtCore.Qt.PointingHandCursor)

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
        accent = "#6366F1"
        if t == "light":
            title_color = "#111827"
            subtitle_color = "#475569"
            helper_color = "#475569"
            line_bg = "#FFFFFF"
            line_border = "#E2E8F0"
            line_text = "#0F172A"
            background = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F8FAFC, stop:1 #E2E8F0)"
            card_bg = "#FFFFFF"
            card_border = "#E2E8F0"
            badge_bg = "#EEF2FF"
            badge_text = "#4338CA"
        else:
            title_color = "#F8FAFC"
            subtitle_color = "#A5B4C3"
            helper_color = "#A5B4C3"
            line_bg = "rgba(255, 255, 255, 0.07)"
            line_border = "rgba(255, 255, 255, 0.16)"
            line_text = "#E5E7EB"
            background = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0B1220, stop:1 #0F172A)"
            card_bg = "rgba(16, 24, 40, 0.96)"
            card_border = "rgba(255, 255, 255, 0.08)"
            badge_bg = "rgba(99, 102, 241, 0.18)"
            badge_text = "#E5E7EB"

        return f"""
            QWidget#loginWindow {{
                background: {background};
                color: {line_text};
            }}

            QWidget#loginWindow QWidget#card {{
                background: {card_bg};
                border: 1px solid {card_border};
                border-radius: 18px;
            }}

            QWidget#loginWindow QLabel#badge {{
                color: {badge_text};
                background: {badge_bg};
                padding: 6px 12px;
                border-radius: 12px;
                font-weight: 700;
                letter-spacing: 0.6px;
            }}

            /* Typography */
            QWidget#loginWindow QLabel#title {{
                font-size: 34px;
                font-weight: 700;
                letter-spacing: 0.4px;
                color: {title_color};
            }}
            QWidget#loginWindow QLabel#subtitle {{
                color: {subtitle_color};
                font-size: 13px;
                font-weight: 600;
            }}
            QWidget#loginWindow QLabel#helperText {{
                color: {helper_color};
                font-size: 12px;
            }}

            /* Inputs */
            QWidget#loginWindow QLineEdit {{
                background-color: {line_bg};
                border: 1px solid {line_border};
                border-radius: 12px;
                padding: 12px 14px;
                color: {line_text};
                selection-background-color: {accent};
            }}
            QWidget#loginWindow QLineEdit:focus {{
                border: 1px solid {accent};
            }}

            /* Buttons */
            QWidget#loginWindow QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:1 #4F46E5);
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                font-weight: 700;
                min-width: 120px;
            }}
            QWidget#loginWindow QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6D6FF3, stop:1 #4B44E0); }}
            QWidget#loginWindow QPushButton:pressed {{ background-color: #4338CA; }}
            QWidget#loginWindow QPushButton:disabled {{
                background-color: #2f3545;
                color: #98A1B2;
            }}

            /* Make the theme toggle button transparent (override generic QPushButton rule) */
            QWidget#loginWindow QPushButton#themeToggle {{
                background: transparent;
                color: {line_text};
                border: none;
                padding: 6px; /* compact */
                min-width: 0px;
            }}
            QWidget#loginWindow QPushButton#themeToggle:hover {{
                background: rgba(99, 102, 241, 0.10);
            }}
            QWidget#loginWindow QPushButton#themeToggle:pressed {{
                background: rgba(99, 102, 241, 0.16);
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
