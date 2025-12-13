"""GUI composition (PySide6).

Responsibilities:
    - Configure logging for the GUI
    - Build backend controller with configured dependencies
    - Start the Qt application and orchestrate login -> dashboard flow

The visual widgets live in dedicated modules with one class per file:
    - login_window.LoginWindow
    - dashboard_window.DashboardWindow
"""

from __future__ import annotations

import logging
import os
import sys

from PySide6 import QtWidgets

from budget_analyser.config.settings import load_settings
from budget_analyser.domain.reporting import ReportService
from budget_analyser.infrastructure.column_mappings import IniColumnMappingProvider
from budget_analyser.infrastructure.ini_config import IniAppConfig
from budget_analyser.infrastructure.json_mappings import JsonCategoryMappingProvider
from budget_analyser.infrastructure.statement_repository import CsvStatementRepository
from budget_analyser.presentation.controllers import BackendController
from budget_analyser.presentation.views.dashboard_window import DashboardWindow
from budget_analyser.presentation.views.login_window import LoginWindow


# Log directory under current working directory for simplicity
LOG_DIR = os.path.abspath(os.path.join(os.getcwd(), "logs"))


def _ensure_logger() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("budget_analyser.gui")
    logger.setLevel(logging.INFO)
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        fh = logging.FileHandler(os.path.join(LOG_DIR, "gui_app.log"), encoding="utf-8")
        fmt = logging.Formatter(
            fmt="%(asctime)s | %(levelname).4s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


def _build_controller(logger: logging.Logger) -> BackendController:
    settings = load_settings()
    config = IniAppConfig(path=settings.ini_config_path)
    statement_repo = CsvStatementRepository(statement_dir=settings.statement_dir, config=config)
    column_mappings = IniColumnMappingProvider(config=config)
    category_mappings = JsonCategoryMappingProvider(
        description_to_sub_category_path=settings.description_to_sub_category_path,
        sub_category_to_category_path=settings.sub_category_to_category_path,
    )
    return BackendController(
        statement_repository=statement_repo,
        column_mappings=column_mappings,
        category_mappings=category_mappings,
        report_service=ReportService(),
        logger=logger,
    )


def run_app() -> int:
    logger = _ensure_logger()
    logger.info("Starting GUI application")

    app = QtWidgets.QApplication(sys.argv)

    # Build controller for reports on demand after login
    controller = _build_controller(logger)

    login = LoginWindow(logger)

    def _on_success():
        # Compute reports and open dashboard
        try:
            reports = controller.run()
        except Exception:  # pylint: disable=broad-except
            logger.exception("Error generating reports")
            QtWidgets.QMessageBox.critical(login, "Error", "Failed to generate reports. See logs.")
            return

        dash = DashboardWindow(reports, logger)
        dash.showMaximized()
        login.close()

    login.login_successful.connect(_on_success)
    login.show()

    rc = app.exec()
    logger.info("GUI application exited with code %s", rc)
    return rc


if __name__ == "__main__":
    raise SystemExit(run_app())
