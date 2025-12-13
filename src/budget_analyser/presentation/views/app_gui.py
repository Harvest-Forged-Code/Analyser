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
import platform
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from PySide6 import QtWidgets

from budget_analyser.config.settings import load_settings
from budget_analyser.config.preferences import AppPreferences
from budget_analyser.domain.reporting import ReportService
from budget_analyser.infrastructure.column_mappings import IniColumnMappingProvider
from budget_analyser.infrastructure.ini_config import IniAppConfig
from budget_analyser.infrastructure.json_mappings import JsonCategoryMappingProvider
from budget_analyser.infrastructure.statement_repository import CsvStatementRepository
from budget_analyser.presentation.controllers import BackendController
from budget_analyser.presentation.views.dashboard_window import DashboardWindow
from budget_analyser.presentation.views.login_window import LoginWindow
from budget_analyser.presentation.views.styles import app_stylesheet, select_app_font

def _logs_dir() -> Path:
    """Return user-writable logs directory with optional env override.

    Order of precedence:
      1) BUDGET_ANALYSER_LOG_DIR (if set)
      2) ~/.budget_analyser/logs
    """
    env_dir = os.environ.get("BUDGET_ANALYSER_LOG_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return Path.home() / ".budget_analyser" / "logs"


def _ensure_logger() -> logging.Logger:
    log_dir = _logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("budget_analyser.gui")
    logger.setLevel(logging.INFO)
    # Avoid duplicate handlers if called multiple times
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        fh = RotatingFileHandler(
            filename=str(log_dir / "gui_app.log"),
            encoding="utf-8",
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
        )
        fmt = logging.Formatter(
            fmt="%(asctime)s | %(levelname).4s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


def _build_controller(logger: logging.Logger) -> BackendController:
    settings = load_settings()
    config = IniAppConfig(path=settings.ini_config_path)
    statement_repo = CsvStatementRepository(
        statement_dir=settings.statement_dir, config=config, logger=logger
    )
    column_mappings = IniColumnMappingProvider(config=config)
    category_mappings = JsonCategoryMappingProvider(
        description_to_sub_category_path=settings.description_to_sub_category_path,
        sub_category_to_category_path=settings.sub_category_to_category_path,
        logger=logger,
    )
    return BackendController(
        statement_repository=statement_repo,
        column_mappings=column_mappings,
        category_mappings=category_mappings,
        report_service=ReportService(),
        logger=logger,
    )


def run_app() -> int:
    # Load settings and preferences first so we can apply log level
    settings = load_settings()
    prefs = AppPreferences(settings.ini_config_path)

    logger = _ensure_logger()
    # Apply persisted log level (defaults to INFO)
    try:
        logger.setLevel(getattr(logging, prefs.get_log_level()))
    except Exception:  # safe guard; keep INFO if invalid
        logger.setLevel(logging.INFO)
    log_file = _logs_dir() / "gui_app.log"
    logger.info("Starting GUI application")
    # Startup diagnostics (single line per item to keep readable)
    try:
        logger.info("Log file: %s", log_file)
        logger.info(
            "Settings: statement_dir=%s | ini=%s | desc_map=%s | subcat_map=%s",
            settings.statement_dir,
            settings.ini_config_path,
            settings.description_to_sub_category_path,
            settings.sub_category_to_category_path,
        )
        logger.info(
            "Platform: %s | Python: %s | CWD: %s",
            platform.platform(),
            sys.version.split(" ")[0],
            os.getcwd(),
        )
    except Exception:
        pass

    app = QtWidgets.QApplication(sys.argv)
    # Set a platform-available UI font to avoid Qt aliasing warnings and costs
    try:
        app.setFont(select_app_font())
        try:
            logger.info("UI font selected: %s", app.font().family())
        except Exception:
            pass
    except Exception:
        pass

    # Apply persisted theme
    theme = prefs.get_theme()
    app.setStyleSheet(app_stylesheet(theme))

    # Build controller for reports on demand after login
    controller = _build_controller(logger)

    # Inject password verification backed by preferences (falls back to 123456)
    login = LoginWindow(logger, verify_password=prefs.verify_password, current_theme=theme)

    def _toggle_theme_from_login() -> None:
        nonlocal theme
        theme = "light" if theme == "dark" else "dark"
        prefs.set_theme(theme)
        app.setStyleSheet(app_stylesheet(theme))
        # inform login to update its toggle icon
        try:
            login.set_theme_indicator(theme)
        except Exception:
            pass

    def _on_success():
        # Compute reports and open dashboard
        try:
            reports = controller.run()
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Error generating reports")
            # Include the log file path and brief details in the dialog
            QtWidgets.QMessageBox.critical(
                login,
                "Error",
                (
                    "Failed to generate reports.\n\n"
                    f"See logs at:\n{log_file}\n\n"
                    f"Details: {exc.__class__.__name__}: {exc}"
                ),
            )
            return

        # Keep a strong reference to the dashboard to prevent it from being
        # garbage-collected after this function returns. Without this, the
        # window may not remain visible on some platforms/PySide versions.
        logger.info("Opening dashboard window with %d monthly reports", len(reports))
        dash = DashboardWindow(reports, logger, prefs)
        app._dashboard = dash  # type: ignore[attr-defined]
        dash.showMaximized()
        login.close()

    login.login_successful.connect(_on_success)
    # Theme toggle from login
    try:
        login.theme_toggle_requested.connect(_toggle_theme_from_login)
    except Exception:
        pass
    login.show()

    rc = app.exec()
    logger.info("GUI application exited with code %s", rc)
    return rc


if __name__ == "__main__":
    raise SystemExit(run_app())
