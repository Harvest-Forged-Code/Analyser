"""Base components and utilities for modern page design.

Provides consistent styling, spacing, and UI components across all pages.
"""
from __future__ import annotations

from PySide6 import QtWidgets, QtCore

from budget_analyser.views.icons import AppIcon, get_icon_pixmap, ICON_SIZE_XLARGE


class ModernPageMixin:
    """Mixin providing modern page layout utilities."""

    @staticmethod
    def create_page_header(
        title: str,
        subtitle: str = "",
        icon: str | AppIcon = "",
    ) -> QtWidgets.QWidget:
        """Create a modern page header with icon, title, and subtitle.

        Args:
            title: Page title text
            subtitle: Optional subtitle/description
            icon: Optional emoji string or AppIcon enum

        Returns:
            Widget containing the formatted header
        """
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        if icon:
            icon_label = QtWidgets.QLabel()
            if isinstance(icon, AppIcon):
                # Use AppIcon - render as pixmap
                pixmap = get_icon_pixmap(icon, color="#A78BFA", size=ICON_SIZE_XLARGE)
                icon_label.setPixmap(pixmap)
                icon_label.setFixedSize(ICON_SIZE_XLARGE, ICON_SIZE_XLARGE)
            else:
                # Use emoji string
                icon_label.setText(icon)
                icon_label.setStyleSheet("font-size: 28px;")
            layout.addWidget(icon_label)

        title_container = QtWidgets.QWidget()
        title_layout = QtWidgets.QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        title_label = QtWidgets.QLabel(title)
        title_font = title_label.font()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #F5F3FF;")
        title_layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QtWidgets.QLabel(subtitle)
            subtitle_label.setWordWrap(True)
            subtitle_label.setStyleSheet("font-size: 13px; color: #A78BFA;")
            title_layout.addWidget(subtitle_label)

        layout.addWidget(title_container, 1)

        return container

    @staticmethod
    def create_controls_row() -> tuple[QtWidgets.QWidget, QtWidgets.QHBoxLayout]:
        """Create a controls row container with consistent spacing.

        Returns:
            Tuple of (container widget, layout) for adding controls
        """
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        return container, layout

    @staticmethod
    def create_control_label(text: str) -> QtWidgets.QLabel:
        """Create a consistently styled control label.

        Args:
            text: Label text

        Returns:
            Styled QLabel
        """
        label = QtWidgets.QLabel(text)
        label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #DDD6FE;
            letter-spacing: 0.3px;
        """)
        return label

    @staticmethod
    def create_card(title: str = "") -> tuple[QtWidgets.QWidget, QtWidgets.QVBoxLayout]:
        """Create a modern card container.

        Args:
            title: Optional card title

        Returns:
            Tuple of (card widget, layout)
        """
        card = QtWidgets.QWidget()
        card.setObjectName("modernCard")
        card.setStyleSheet("""
            QWidget#modernCard {
                background: rgba(18, 18, 20, 0.95);
                border: 1px solid rgba(60, 60, 70, 0.3);
                border-radius: 18px;
            }
        """)

        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        if title:
            title_label = QtWidgets.QLabel(title.upper())
            title_label.setStyleSheet("""
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
                color: #8B5CF6;
            """)
            layout.addWidget(title_label)

        return card, layout

    @staticmethod
    def style_combo_box(combo: QtWidgets.QComboBox, min_height: int = 30) -> None:
        """Apply consistent styling to a combobox.

        Args:
            combo: QComboBox to style
            min_height: Minimum height in pixels
        """
        combo.setMinimumHeight(min_height)

    @staticmethod
    def style_date_edit(date_edit: QtWidgets.QDateEdit, min_height: int = 40) -> None:
        """Apply consistent styling to a date edit widget.

        Args:
            date_edit: QDateEdit to style
            min_height: Minimum height in pixels
        """
        date_edit.setMinimumHeight(min_height)
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("MM/dd/yyyy")

    @staticmethod
    def create_action_button(text: str, primary: bool = False) -> QtWidgets.QPushButton:
        """Create a styled action button.

        Args:
            text: Button text
            primary: Whether this is a primary action button

        Returns:
            Styled QPushButton
        """
        button = QtWidgets.QPushButton(text)
        button.setMinimumHeight(44)
        button.setMinimumWidth(100)

        if not primary:
            button.setObjectName("secondaryActionButton")
            button.setStyleSheet("""
                QPushButton#secondaryActionButton {
                    background: rgba(139, 92, 246, 0.15);
                    border: 1px solid rgba(139, 92, 246, 0.25);
                    color: #DDD6FE;
                    font-weight: 600;
                }
                QPushButton#secondaryActionButton:hover {
                    background: rgba(139, 92, 246, 0.25);
                    border-color: rgba(139, 92, 246, 0.35);
                }
            """)

        return button

    @staticmethod
    def create_scroll_area() -> tuple[QtWidgets.QScrollArea, QtWidgets.QWidget]:
        """Create a scroll area with consistent styling.

        Returns:
            Tuple of (scroll area, content container)
        """
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        container = QtWidgets.QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)

        return scroll, container
