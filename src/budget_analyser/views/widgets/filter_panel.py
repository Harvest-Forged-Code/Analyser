"""Advanced filtering panel widget for transaction filtering.

Purpose:
    Provides a comprehensive filtering UI with:
    - Amount range (min/max)
    - Date range with presets
    - Multi-select category/sub-category
    - Account filter
    - Mapped/Unmapped toggle

This widget emits signals when filters change, allowing parent widgets
to react and filter their data accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Set, Callable, Any

from PySide6 import QtCore, QtWidgets

from budget_analyser.views.pages._page_base import ModernPageMixin


@dataclass
class FilterCriteria:
    """Data class holding all filter criteria."""

    # Amount range
    amount_min: float | None = None
    amount_max: float | None = None

    # Date range
    date_from: date | None = None
    date_to: date | None = None

    # Categories (empty means all)
    categories: Set[str] = field(default_factory=set)
    sub_categories: Set[str] = field(default_factory=set)

    # Account filter (empty means all)
    accounts: Set[str] = field(default_factory=set)

    # Mapping status
    show_mapped: bool = True
    show_unmapped: bool = True

    # Text search
    search_text: str = ""

    def is_empty(self) -> bool:
        """Check if no filters are applied."""
        return (
            self.amount_min is None
            and self.amount_max is None
            and self.date_from is None
            and self.date_to is None
            and not self.categories
            and not self.sub_categories
            and not self.accounts
            and self.show_mapped
            and self.show_unmapped
            and not self.search_text
        )

    def matches_amount(self, amount: float) -> bool:
        """Check if amount passes the filter."""
        if self.amount_min is not None and amount < self.amount_min:
            return False
        if self.amount_max is not None and amount > self.amount_max:
            return False
        return True

    def matches_date(self, txn_date: date) -> bool:
        """Check if date passes the filter."""
        if self.date_from is not None and txn_date < self.date_from:
            return False
        if self.date_to is not None and txn_date > self.date_to:
            return False
        return True

    def matches_category(self, category: str) -> bool:
        """Check if category passes the filter."""
        if not self.categories:
            return True
        return category in self.categories

    def matches_sub_category(self, sub_category: str) -> bool:
        """Check if sub-category passes the filter."""
        if not self.sub_categories:
            return True
        return sub_category in self.sub_categories

    def matches_account(self, account: str) -> bool:
        """Check if account passes the filter."""
        if not self.accounts:
            return True
        return account in self.accounts

    def matches_mapping_status(self, is_mapped: bool) -> bool:
        """Check if mapping status passes the filter."""
        if is_mapped:
            return self.show_mapped
        return self.show_unmapped

    def matches_search(self, text: str) -> bool:
        """Check if text contains the search term."""
        if not self.search_text:
            return True
        return self.search_text.lower() in text.lower()


class DatePreset:
    """Date range presets for quick filtering."""

    @staticmethod
    def this_month() -> tuple[date, date]:
        """Get date range for current month."""
        today = date.today()
        first_day = today.replace(day=1)
        return first_day, today

    @staticmethod
    def last_month() -> tuple[date, date]:
        """Get date range for previous month."""
        today = date.today()
        first_of_current = today.replace(day=1)
        last_of_previous = first_of_current - timedelta(days=1)
        first_of_previous = last_of_previous.replace(day=1)
        return first_of_previous, last_of_previous

    @staticmethod
    def last_3_months() -> tuple[date, date]:
        """Get date range for last 3 months."""
        today = date.today()
        three_months_ago = today - timedelta(days=90)
        return three_months_ago, today

    @staticmethod
    def last_6_months() -> tuple[date, date]:
        """Get date range for last 6 months."""
        today = date.today()
        six_months_ago = today - timedelta(days=180)
        return six_months_ago, today

    @staticmethod
    def this_year() -> tuple[date, date]:
        """Get date range for current year."""
        today = date.today()
        first_of_year = today.replace(month=1, day=1)
        return first_of_year, today

    @staticmethod
    def last_year() -> tuple[date, date]:
        """Get date range for previous year."""
        today = date.today()
        last_year = today.year - 1
        first_of_last_year = date(last_year, 1, 1)
        last_of_last_year = date(last_year, 12, 31)
        return first_of_last_year, last_of_last_year

    @staticmethod
    def all_time() -> tuple[None, None]:
        """No date restriction."""
        return None, None


class MultiSelectComboBox(QtWidgets.QComboBox):
    """Combo box that allows multiple selections."""

    selection_changed = QtCore.Signal(set)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: List[str] = []
        self._checked: Set[str] = set()

        # Use custom view for multi-select
        self.setView(QtWidgets.QListView())
        self.view().pressed.connect(self._handle_item_pressed)

        # Prevent popup from closing on selection
        self.view().viewport().installEventFilter(self)

        self._update_display()

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Prevent popup from closing on item click."""
        if obj == self.view().viewport() and event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            return True
        return super().eventFilter(obj, event)

    def set_items(self, items: List[str]) -> None:
        """Set the available items."""
        self._items = sorted(items)
        self._checked.clear()
        self._rebuild_items()
        self._update_display()

    def _rebuild_items(self) -> None:
        """Rebuild combo box items."""
        self.clear()
        for item in self._items:
            self.addItem(item)
            idx = self.count() - 1
            self.setItemData(idx, QtCore.Qt.CheckState.Unchecked, QtCore.Qt.ItemDataRole.CheckStateRole)

    def _handle_item_pressed(self, index: QtCore.QModelIndex) -> None:
        """Handle item click to toggle selection."""
        item_text = self._items[index.row()]

        if item_text in self._checked:
            self._checked.discard(item_text)
            self.setItemData(
                index.row(),
                QtCore.Qt.CheckState.Unchecked,
                QtCore.Qt.ItemDataRole.CheckStateRole
            )
        else:
            self._checked.add(item_text)
            self.setItemData(
                index.row(),
                QtCore.Qt.CheckState.Checked,
                QtCore.Qt.ItemDataRole.CheckStateRole
            )

        self._update_display()
        self.selection_changed.emit(self._checked.copy())

    def _update_display(self) -> None:
        """Update the display text."""
        if not self._checked:
            self.setEditText("All")
        elif len(self._checked) == 1:
            self.setEditText(next(iter(self._checked)))
        else:
            self.setEditText(f"{len(self._checked)} selected")

    def get_selected(self) -> Set[str]:
        """Get the currently selected items."""
        return self._checked.copy()

    def clear_selection(self) -> None:
        """Clear all selections."""
        self._checked.clear()
        self._rebuild_items()
        self._update_display()
        self.selection_changed.emit(set())


class AdvancedFilterPanel(QtWidgets.QWidget):
    """Advanced filtering panel with multiple filter types."""

    # Signal emitted when any filter changes
    filters_changed = QtCore.Signal(FilterCriteria)

    def __init__(
        self,
        categories: List[str] | None = None,
        sub_categories: List[str] | None = None,
        accounts: List[str] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._categories = categories or []
        self._sub_categories = sub_categories or []
        self._accounts = accounts or []
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the filter panel UI."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        # Create collapsible card for filters
        card, card_layout = ModernPageMixin.create_card("FILTERS")

        # Filter grid
        filter_grid = QtWidgets.QGridLayout()
        filter_grid.setSpacing(16)
        filter_grid.setColumnStretch(1, 1)
        filter_grid.setColumnStretch(3, 1)
        filter_grid.setColumnStretch(5, 1)

        row = 0

        # Search text
        search_label = QtWidgets.QLabel("Search:")
        search_label.setStyleSheet("color: #4B5563; font-weight: 500;")
        self._search_input = QtWidgets.QLineEdit()
        self._search_input.setPlaceholderText("Search descriptions...")
        self._search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: white;
                color: #1F2937;
            }
            QLineEdit:focus {
                border-color: #8B5CF6;
            }
        """)
        self._search_input.textChanged.connect(self._on_filter_change)
        filter_grid.addWidget(search_label, row, 0)
        filter_grid.addWidget(self._search_input, row, 1, 1, 5)
        row += 1

        # Amount range
        amount_label = QtWidgets.QLabel("Amount:")
        amount_label.setStyleSheet("color: #4B5563; font-weight: 500;")

        amount_layout = QtWidgets.QHBoxLayout()
        self._amount_min = QtWidgets.QDoubleSpinBox()
        self._amount_min.setRange(-1000000, 1000000)
        self._amount_min.setSpecialValueText("Min")
        self._amount_min.setValue(self._amount_min.minimum())
        self._amount_min.setPrefix("$")
        self._amount_min.setStyleSheet(self._spinbox_style())
        self._amount_min.valueChanged.connect(self._on_filter_change)

        amount_to_label = QtWidgets.QLabel("to")
        amount_to_label.setStyleSheet("color: #6B7280;")

        self._amount_max = QtWidgets.QDoubleSpinBox()
        self._amount_max.setRange(-1000000, 1000000)
        self._amount_max.setSpecialValueText("Max")
        self._amount_max.setValue(self._amount_max.maximum())
        self._amount_max.setPrefix("$")
        self._amount_max.setStyleSheet(self._spinbox_style())
        self._amount_max.valueChanged.connect(self._on_filter_change)

        amount_layout.addWidget(self._amount_min)
        amount_layout.addWidget(amount_to_label)
        amount_layout.addWidget(self._amount_max)
        amount_layout.addStretch()

        filter_grid.addWidget(amount_label, row, 0)
        filter_grid.addLayout(amount_layout, row, 1, 1, 2)

        # Date range
        date_label = QtWidgets.QLabel("Date:")
        date_label.setStyleSheet("color: #4B5563; font-weight: 500;")

        date_layout = QtWidgets.QHBoxLayout()
        self._date_from = QtWidgets.QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setSpecialValueText("From")
        self._date_from.setDate(QtCore.QDate(2000, 1, 1))
        self._date_from.setStyleSheet(self._dateedit_style())
        self._date_from.dateChanged.connect(self._on_filter_change)

        date_to_label = QtWidgets.QLabel("to")
        date_to_label.setStyleSheet("color: #6B7280;")

        self._date_to = QtWidgets.QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setSpecialValueText("To")
        self._date_to.setDate(QtCore.QDate.currentDate())
        self._date_to.setStyleSheet(self._dateedit_style())
        self._date_to.dateChanged.connect(self._on_filter_change)

        date_layout.addWidget(self._date_from)
        date_layout.addWidget(date_to_label)
        date_layout.addWidget(self._date_to)
        date_layout.addStretch()

        filter_grid.addWidget(date_label, row, 3)
        filter_grid.addLayout(date_layout, row, 4, 1, 2)
        row += 1

        # Date presets
        preset_label = QtWidgets.QLabel("Quick:")
        preset_label.setStyleSheet("color: #4B5563; font-weight: 500;")

        preset_layout = QtWidgets.QHBoxLayout()
        preset_layout.setSpacing(8)

        presets = [
            ("This Month", DatePreset.this_month),
            ("Last Month", DatePreset.last_month),
            ("Last 3M", DatePreset.last_3_months),
            ("This Year", DatePreset.this_year),
            ("All", DatePreset.all_time),
        ]

        for preset_name, preset_func in presets:
            btn = QtWidgets.QPushButton(preset_name)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F3F4F6;
                    border: 1px solid #E5E7EB;
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: #4B5563;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #E5E7EB;
                }
                QPushButton:pressed {
                    background-color: #D1D5DB;
                }
            """)
            btn.clicked.connect(lambda checked, f=preset_func: self._apply_date_preset(f))
            preset_layout.addWidget(btn)

        preset_layout.addStretch()
        filter_grid.addWidget(preset_label, row, 0)
        filter_grid.addLayout(preset_layout, row, 1, 1, 5)
        row += 1

        # Category filter
        cat_label = QtWidgets.QLabel("Category:")
        cat_label.setStyleSheet("color: #4B5563; font-weight: 500;")
        self._category_combo = MultiSelectComboBox()
        self._category_combo.set_items(self._categories)
        self._category_combo.setStyleSheet(self._combo_style())
        self._category_combo.selection_changed.connect(self._on_filter_change)
        filter_grid.addWidget(cat_label, row, 0)
        filter_grid.addWidget(self._category_combo, row, 1)

        # Sub-category filter
        subcat_label = QtWidgets.QLabel("Sub-category:")
        subcat_label.setStyleSheet("color: #4B5563; font-weight: 500;")
        self._subcategory_combo = MultiSelectComboBox()
        self._subcategory_combo.set_items(self._sub_categories)
        self._subcategory_combo.setStyleSheet(self._combo_style())
        self._subcategory_combo.selection_changed.connect(self._on_filter_change)
        filter_grid.addWidget(subcat_label, row, 2)
        filter_grid.addWidget(self._subcategory_combo, row, 3)

        # Account filter
        account_label = QtWidgets.QLabel("Account:")
        account_label.setStyleSheet("color: #4B5563; font-weight: 500;")
        self._account_combo = MultiSelectComboBox()
        self._account_combo.set_items(self._accounts)
        self._account_combo.setStyleSheet(self._combo_style())
        self._account_combo.selection_changed.connect(self._on_filter_change)
        filter_grid.addWidget(account_label, row, 4)
        filter_grid.addWidget(self._account_combo, row, 5)
        row += 1

        # Mapping status toggles
        status_label = QtWidgets.QLabel("Status:")
        status_label.setStyleSheet("color: #4B5563; font-weight: 500;")

        status_layout = QtWidgets.QHBoxLayout()
        self._show_mapped = QtWidgets.QCheckBox("Mapped")
        self._show_mapped.setChecked(True)
        self._show_mapped.setStyleSheet(self._checkbox_style())
        self._show_mapped.stateChanged.connect(self._on_filter_change)

        self._show_unmapped = QtWidgets.QCheckBox("Unmapped")
        self._show_unmapped.setChecked(True)
        self._show_unmapped.setStyleSheet(self._checkbox_style())
        self._show_unmapped.stateChanged.connect(self._on_filter_change)

        status_layout.addWidget(self._show_mapped)
        status_layout.addWidget(self._show_unmapped)
        status_layout.addStretch()

        filter_grid.addWidget(status_label, row, 0)
        filter_grid.addLayout(status_layout, row, 1, 1, 2)

        # Clear filters button
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()

        self._clear_btn = QtWidgets.QPushButton("Clear All Filters")
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEE2E2;
                border: 1px solid #FECACA;
                border-radius: 6px;
                padding: 8px 16px;
                color: #DC2626;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #FECACA;
            }
        """)
        self._clear_btn.clicked.connect(self.clear_filters)
        btn_layout.addWidget(self._clear_btn)

        filter_grid.addLayout(btn_layout, row, 4, 1, 2)

        card_layout.addLayout(filter_grid)
        main_layout.addWidget(card)

    def _spinbox_style(self) -> str:
        """Return stylesheet for spinboxes."""
        return """
            QDoubleSpinBox {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 6px 10px;
                background-color: white;
                color: #1F2937;
                min-width: 100px;
            }
            QDoubleSpinBox:focus {
                border-color: #8B5CF6;
            }
        """

    def _dateedit_style(self) -> str:
        """Return stylesheet for date edits."""
        return """
            QDateEdit {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 6px 10px;
                background-color: white;
                color: #1F2937;
                min-width: 120px;
            }
            QDateEdit:focus {
                border-color: #8B5CF6;
            }
            QDateEdit::drop-down {
                border: none;
                width: 20px;
            }
        """

    def _combo_style(self) -> str:
        """Return stylesheet for combo boxes."""
        return """
            QComboBox {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 6px 10px;
                background-color: white;
                color: #1F2937;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #8B5CF6;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #E5E7EB;
                background-color: white;
                selection-background-color: #EDE9FE;
            }
        """

    def _checkbox_style(self) -> str:
        """Return stylesheet for checkboxes."""
        return """
            QCheckBox {
                color: #4B5563;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #D1D5DB;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #8B5CF6;
                border-color: #8B5CF6;
            }
            QCheckBox::indicator:hover {
                border-color: #8B5CF6;
            }
        """

    def _apply_date_preset(self, preset_func: Callable[[], tuple]) -> None:
        """Apply a date preset."""
        date_from, date_to = preset_func()

        if date_from is None:
            self._date_from.setDate(QtCore.QDate(2000, 1, 1))
        else:
            self._date_from.setDate(QtCore.QDate(date_from.year, date_from.month, date_from.day))

        if date_to is None:
            self._date_to.setDate(QtCore.QDate.currentDate())
        else:
            self._date_to.setDate(QtCore.QDate(date_to.year, date_to.month, date_to.day))

        self._on_filter_change()

    def _on_filter_change(self, *args: Any) -> None:
        """Handle any filter change."""
        criteria = self.get_criteria()
        self.filters_changed.emit(criteria)

    def get_criteria(self) -> FilterCriteria:
        """Get the current filter criteria."""
        # Amount range
        amount_min = None
        if self._amount_min.value() > self._amount_min.minimum():
            amount_min = self._amount_min.value()

        amount_max = None
        if self._amount_max.value() < self._amount_max.maximum():
            amount_max = self._amount_max.value()

        # Date range
        date_from = None
        from_qdate = self._date_from.date()
        if from_qdate > QtCore.QDate(2000, 1, 1):
            date_from = date(from_qdate.year(), from_qdate.month(), from_qdate.day())

        date_to = None
        to_qdate = self._date_to.date()
        today = QtCore.QDate.currentDate()
        if to_qdate < today:
            date_to = date(to_qdate.year(), to_qdate.month(), to_qdate.day())

        return FilterCriteria(
            amount_min=amount_min,
            amount_max=amount_max,
            date_from=date_from,
            date_to=date_to,
            categories=self._category_combo.get_selected(),
            sub_categories=self._subcategory_combo.get_selected(),
            accounts=self._account_combo.get_selected(),
            show_mapped=self._show_mapped.isChecked(),
            show_unmapped=self._show_unmapped.isChecked(),
            search_text=self._search_input.text().strip(),
        )

    def clear_filters(self) -> None:
        """Clear all filters to default state."""
        self._search_input.clear()
        self._amount_min.setValue(self._amount_min.minimum())
        self._amount_max.setValue(self._amount_max.maximum())
        self._date_from.setDate(QtCore.QDate(2000, 1, 1))
        self._date_to.setDate(QtCore.QDate.currentDate())
        self._category_combo.clear_selection()
        self._subcategory_combo.clear_selection()
        self._account_combo.clear_selection()
        self._show_mapped.setChecked(True)
        self._show_unmapped.setChecked(True)
        self._on_filter_change()

    def set_categories(self, categories: List[str]) -> None:
        """Update the available categories."""
        self._categories = categories
        self._category_combo.set_items(categories)

    def set_sub_categories(self, sub_categories: List[str]) -> None:
        """Update the available sub-categories."""
        self._sub_categories = sub_categories
        self._subcategory_combo.set_items(sub_categories)

    def set_accounts(self, accounts: List[str]) -> None:
        """Update the available accounts."""
        self._accounts = accounts
        self._account_combo.set_items(accounts)


class CollapsibleFilterPanel(QtWidgets.QWidget):
    """Collapsible wrapper for the advanced filter panel."""

    filters_changed = QtCore.Signal(FilterCriteria)

    def __init__(
        self,
        categories: List[str] | None = None,
        sub_categories: List[str] | None = None,
        accounts: List[str] | None = None,
        collapsed: bool = True,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._collapsed = collapsed
        self._init_ui(categories, sub_categories, accounts)

    def _init_ui(
        self,
        categories: List[str] | None,
        sub_categories: List[str] | None,
        accounts: List[str] | None,
    ) -> None:
        """Initialize the collapsible panel UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Toggle button
        self._toggle_btn = QtWidgets.QPushButton(
            "▼ Show Filters" if self._collapsed else "▲ Hide Filters"
        )
        self._toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 8px 16px;
                color: #6B7280;
                font-weight: 500;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                color: #4B5563;
            }
        """)
        self._toggle_btn.clicked.connect(self._toggle_panel)
        layout.addWidget(self._toggle_btn)

        # Filter panel
        self._filter_panel = AdvancedFilterPanel(
            categories=categories,
            sub_categories=sub_categories,
            accounts=accounts,
        )
        self._filter_panel.filters_changed.connect(self.filters_changed.emit)
        self._filter_panel.setVisible(not self._collapsed)
        layout.addWidget(self._filter_panel)

    def _toggle_panel(self) -> None:
        """Toggle panel visibility."""
        self._collapsed = not self._collapsed
        self._filter_panel.setVisible(not self._collapsed)
        self._toggle_btn.setText(
            "▼ Show Filters" if self._collapsed else "▲ Hide Filters"
        )

    def get_criteria(self) -> FilterCriteria:
        """Get the current filter criteria."""
        return self._filter_panel.get_criteria()

    def clear_filters(self) -> None:
        """Clear all filters."""
        self._filter_panel.clear_filters()

    def set_categories(self, categories: List[str]) -> None:
        """Update available categories."""
        self._filter_panel.set_categories(categories)

    def set_sub_categories(self, sub_categories: List[str]) -> None:
        """Update available sub-categories."""
        self._filter_panel.set_sub_categories(sub_categories)

    def set_accounts(self, accounts: List[str]) -> None:
        """Update available accounts."""
        self._filter_panel.set_accounts(accounts)
