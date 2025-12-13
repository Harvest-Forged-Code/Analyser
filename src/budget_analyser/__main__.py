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
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return logging.getLogger("budget_analyser")


def main() -> None:
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


if __name__ == "__main__":
    main()
