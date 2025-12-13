"""Application composition root.

Default behavior:
    Launch the PySide6 GUI application (fullscreen login -> dashboard).

For the previous CLI renderer, import and call `run_cli()` from this module.
"""

from __future__ import annotations

import logging

from budget_analyser.config.settings import load_settings
from budget_analyser.domain.reporting import ReportService
from budget_analyser.infrastructure.column_mappings import IniColumnMappingProvider
from budget_analyser.infrastructure.ini_config import IniAppConfig
from budget_analyser.infrastructure.json_mappings import JsonCategoryMappingProvider
from budget_analyser.infrastructure.statement_repository import CsvStatementRepository
from budget_analyser.presentation.controllers import BackendController
from budget_analyser.presentation.views.cli import CliView
from budget_analyser.presentation.views.app_gui import run_app as run_gui


def _configure_logging(*, level: str) -> logging.Logger:
    """Configure the standard library logging.

    Args:
        level: Log level name (e.g., "INFO", "DEBUG"). Unknown values default to INFO.

    Returns:
        A configured logger for the application namespace.
    """
    # Configure global logging handlers/formatters once.
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname).4s | %(name)s | %(filename)s:%(lineno)d | | %(message)s",
    )
    # Return an app-specific logger instance.
    return logging.getLogger("budget_analyser")


def run_cli() -> None:
    """Run the application via CLI renderer (legacy mode)."""
    settings = load_settings()
    logger = _configure_logging(level=settings.log_level)

    config = IniAppConfig(path=settings.ini_config_path)
    statement_repo = CsvStatementRepository(statement_dir=settings.statement_dir, config=config)
    column_mappings = IniColumnMappingProvider(config=config)
    category_mappings = JsonCategoryMappingProvider(
        description_to_sub_category_path=settings.description_to_sub_category_path,
        sub_category_to_category_path=settings.sub_category_to_category_path,
    )

    controller = BackendController(
        statement_repository=statement_repo,
        column_mappings=column_mappings,
        category_mappings=category_mappings,
        report_service=ReportService(),
        logger=logger,
    )

    view = CliView()
    view.render(reports=controller.run())


def main() -> None:
    """Run the PySide6 GUI application by default."""
    run_gui()


if __name__ == "__main__":
    main()
