"""Application composition root.

Purpose:
    Wire together infrastructure + domain + presentation dependencies in one place.

Goal:
    Keep dependency injection out of the domain and presentation layers.

Steps:
    1. Load settings from environment / optional .env.
    2. Configure logging.
    3. Build adapters (INI config, CSV repo, JSON mappers).
    4. Build controller + view and run the app.
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
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    # Return an app-specific logger instance.
    return logging.getLogger("budget_analyser")


def main() -> None:
    """Run the application via CLI.

    Steps:
        1. Load runtime settings.
        2. Build dependencies.
        3. Execute the backend workflow.
        4. Render results to stdout.
    """
    # Load settings (env + optional .env) and configure logging.
    settings = load_settings()
    logger = _configure_logging(level=settings.log_level)

    # Build infrastructure adapters.
    config = IniAppConfig(path=settings.ini_config_path)
    statement_repo = CsvStatementRepository(statement_dir=settings.statement_dir, config=config)
    column_mappings = IniColumnMappingProvider(config=config)
    category_mappings = JsonCategoryMappingProvider(
        description_to_sub_category_path=settings.description_to_sub_category_path,
        sub_category_to_category_path=settings.sub_category_to_category_path,
    )

    # Wire dependencies into the controller (presentation layer).
    controller = BackendController(
        statement_repository=statement_repo,
        column_mappings=column_mappings,
        category_mappings=category_mappings,
        report_service=ReportService(),
        logger=logger,
    )

    # Render to CLI (view layer).
    view = CliView()
    view.render(reports=controller.run())


if __name__ == "__main__":
    main()
