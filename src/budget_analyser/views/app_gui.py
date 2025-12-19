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

from budget_analyser.settings.settings import load_settings
from budget_analyser.settings.preferences import AppPreferences
from budget_analyser.domain.reporting import ReportService
from budget_analyser.infrastructure.column_mappings import IniColumnMappingProvider
from budget_analyser.infrastructure.ini_config import IniAppConfig
from budget_analyser.infrastructure.json_mappings import (
    JsonCategoryMappingProvider,
    JsonCategoryMappingStore,
)
from budget_analyser.infrastructure.statement_repository import CsvStatementRepository
from budget_analyser.infrastructure.database import (
    TransactionDatabase,
    DatabaseTransactionRepository,
)
from budget_analyser.domain.transaction_ingestion import TransactionIngestionService
from budget_analyser.domain.transaction_processing import CategoryMappers
from budget_analyser.controller.controllers import BackendController
from budget_analyser.views.dashboard_window import DashboardWindow
from budget_analyser.views.login_window import LoginWindow
from budget_analyser.views.styles import app_stylesheet, select_app_font
from budget_analyser.controller import MapperController
from budget_analyser.controller import UploadController

def _package_data_dir() -> Path:
    """Return the package data directory (src/budget_analyser/data)."""
    # app_gui.py lives under src/budget_analyser/views/
    return Path(__file__).resolve().parents[1] / "data"


def _logs_dir() -> Path:
    """Return logs directory with optional env override.

    Order of precedence:
      1) BUDGET_ANALYSER_LOG_DIR (if set)
      2) src/budget_analyser/data/logs/ (application data folder)
    """
    env_dir = os.environ.get("BUDGET_ANALYSER_LOG_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return _package_data_dir() / "logs"


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

    # Build upload controller early to check for missing CSVs
    ini_config = IniAppConfig(path=settings.ini_config_path)

    # Create database and ingestion service for processing uploaded CSVs
    transaction_db = TransactionDatabase(db_path=settings.database_path, logger=logger)
    category_mapping_provider = JsonCategoryMappingProvider(
        description_to_sub_category_path=settings.description_to_sub_category_path,
        sub_category_to_category_path=settings.sub_category_to_category_path,
        logger=logger,
    )
    category_mappers = CategoryMappers(
        description_to_sub_category=category_mapping_provider.description_to_sub_category(),
        sub_category_to_category=category_mapping_provider.sub_category_to_category(),
    )
    ingestion_service = TransactionIngestionService(
        database=transaction_db,
        category_mappers=category_mappers,
        logger=logger,
    )

    upload_controller = UploadController(
        logger=logger,
        ini_config=ini_config,
        statements_dir=settings.statement_dir,
        ingestion_service=ingestion_service,
    )

    def _open_dashboard(reports, csv_missing: bool = False):
        """Open dashboard window with given reports and mode."""
        # Build mapper controller for the Mapper page
        mapping_store = JsonCategoryMappingStore(
            description_to_sub_category_path=settings.description_to_sub_category_path,
            sub_category_to_category_path=settings.sub_category_to_category_path,
            logger=logger,
        )
        mapper_controller = MapperController(reports, logger, mapping_store)

        dash = DashboardWindow(
            reports, logger, prefs, mapper_controller, upload_controller,
            csv_missing=csv_missing,
        )

        # Connect reload signal to handle CSV upload completion
        def _on_reload_requested():
            logger.info("Reload requested after CSV upload")
            # Check if database has data (transactions are stored during upload)
            if db_repository.has_data():
                try:
                    transactions = db_repository.get_processed_transactions()
                    new_reports = controller.run_from_database(transactions)
                    logger.info("Reports regenerated from database with %d months", len(new_reports))
                    # Enable all pages and show success message
                    dash.enable_all_pages()
                    QtWidgets.QMessageBox.information(
                        dash,
                        "Success",
                        f"Transactions processed successfully!\n\n"
                        f"{len(transactions)} transactions loaded.\n"
                        "You can now access all pages. Please restart the app "
                        "to see the updated reports.",
                    )
                except Exception as exc:
                    logger.exception("Error regenerating reports from database")
                    QtWidgets.QMessageBox.warning(
                        dash,
                        "Warning",
                        f"Failed to generate reports:\n{exc}\n\n"
                        "Please restart the app to try again.",
                    )
            else:
                # No database data yet - check missing statements
                missing = upload_controller.get_missing_statements()
                if missing:
                    missing_names = [f"{bank} ({atype})" for bank, atype, _ in missing]
                    logger.info("Still missing statements: %s", ", ".join(missing_names))
                else:
                    logger.info("All statements uploaded but no data in database yet")

        dash.reload_requested.connect(_on_reload_requested)

        # Keep strong reference to prevent garbage collection
        app._dashboard = dash  # type: ignore[attr-defined]
        dash.showMaximized()
        login.close()

    # Create database repository for reading transactions
    db_repository = DatabaseTransactionRepository(database=transaction_db, logger=logger)

    def _on_success():
        # Check if CSVs are missing
        missing_statements = upload_controller.get_missing_statements()

        if missing_statements:
            # CSVs are missing - check if database has data from previous uploads
            if db_repository.has_data():
                logger.info("CSVs missing but database has data - using database")
                try:
                    transactions = db_repository.get_processed_transactions()
                    reports = controller.run_from_database(transactions)
                    logger.info(
                        "Generated %d monthly reports from database", len(reports)
                    )
                    _open_dashboard(reports=reports, csv_missing=False)
                    return
                except Exception as exc:  # pylint: disable=broad-except
                    logger.exception("Error generating reports from database")
                    # Fall through to restricted mode

            # No database data - open dashboard in restricted mode
            missing_names = [f"{bank} ({atype})" for bank, atype, _ in missing_statements]
            logger.warning(
                "Missing CSV statements: %s. Opening in restricted mode.",
                ", ".join(missing_names),
            )
            _open_dashboard(reports=[], csv_missing=True)
        else:
            # All CSVs present - check database first, then ingest CSVs if needed
            try:
                if not db_repository.has_data():
                    # No database data - ingest CSVs to DB first (first run or after DB reset)
                    logger.info("No database data - ingesting CSVs to database")
                    column_mappings = IniColumnMappingProvider(config=ini_config)
                    for section in ("credit_cards", "checking_accounts"):
                        for account in ini_config.list_accounts(section=section):
                            filename = ini_config.get_statement_filename(
                                section=section, account=account
                            )
                            csv_path = settings.statement_dir / filename
                            col_mapping = column_mappings.get_column_mapping(account)
                            logger.info("Ingesting %s from %s", account, csv_path)
                            result = ingestion_service.ingest_csv(
                                csv_path=csv_path,
                                account_name=account,
                                column_mapping=col_mapping,
                            )
                            if result.success:
                                logger.info(
                                    "Ingested %s: %d processed, %d inserted, %d duplicates",
                                    account,
                                    result.transactions_processed,
                                    result.transactions_inserted,
                                    result.duplicates_skipped,
                                )
                            else:
                                logger.error("Failed to ingest %s: %s", account, result.message)

                # Generate reports from database (always DB-centric)
                logger.info("Loading reports from database")
                transactions = db_repository.get_processed_transactions()
                reports = controller.run_from_database(transactions)
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Error generating reports")
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

            logger.info("Opening dashboard window with %d monthly reports", len(reports))
            _open_dashboard(reports=reports, csv_missing=False)

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
