"""Dependency wiring for the FastAPI layer.

Composition root: every feature controller is available as a
FastAPI ``Depends`` callable.  Module-level singletons are
initialised once via ``initialize()`` (called from the lifespan
handler in main.py).
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from budget_analyser.core.models import MonthlyReports
from budget_analyser.settings.settings import load_settings
from budget_analyser.settings.preferences import AppPreferences
from budget_analyser.infrastructure.ini_config import IniAppConfig
from budget_analyser.infrastructure.column_mappings import (
    IniColumnMappingProvider,
)
from budget_analyser.infrastructure.json_mappings import (
    JsonCategoryMappingProvider,
    JsonCashflowMappingProvider,
    JsonCategoryMappingStore,
    JsonCashflowMappingStore,
)
from budget_analyser.infrastructure.statement_repository import (
    CsvStatementRepository,
)
from budget_analyser.infrastructure.database import (
    TransactionDatabase,
    DatabaseTransactionRepository,
)
from budget_analyser.features.reporting.service import ReportService
from budget_analyser.controller.backend_controller import BackendController
from budget_analyser.features.budget_goals.repository import (
    BudgetGoalsRepository,
)
from budget_analyser.features.budget_goals.controller import (
    BudgetGoalsController,
)
from budget_analyser.features.net_worth.repository import (
    NetWorthRepository,
)
from budget_analyser.features.net_worth.controller import (
    NetWorthController,
)
from budget_analyser.features.recurring.repository import (
    RecurringRepository,
)
from budget_analyser.features.recurring.controller import (
    RecurringController,
)
from budget_analyser.features.savings.controller import SavingsController
from budget_analyser.features.ingestion.service import (
    TransactionIngestionService,
)
from budget_analyser.features.ingestion.controller import UploadController
from budget_analyser.features.mappers.mapper_controller import (
    MapperController,
)
from budget_analyser.features.mappers.cashflow_controller import (
    CashflowMapperController,
)
from budget_analyser.features.mappers.sub_category_controller import (
    SubCategoryMapperController,
)
from budget_analyser.features.settings.controller import SettingsController
from budget_analyser.features.reporting.earnings_controller import (
    EarningsStatsController,
)
from budget_analyser.features.reporting.expenses_controller import (
    ExpensesStatsController,
)
from budget_analyser.features.payments.controller import (
    PaymentsReconciliationController,
)
from budget_analyser.domain.category_mappers import CategoryMappers

# ---------------------------------------------------------------------------
# Module-level singletons (set by ``initialize()``)
# ---------------------------------------------------------------------------

_logger: logging.Logger | None = None
_prefs: AppPreferences | None = None
_backend_controller: BackendController | None = None
_db_repository: DatabaseTransactionRepository | None = None
_upload_controller: UploadController | None = None

_budget_goals_controller: BudgetGoalsController | None = None
_net_worth_controller: NetWorthController | None = None
_recurring_controller: RecurringController | None = None
_savings_controller: SavingsController | None = None
_earnings_stats_controller: EarningsStatsController | None = None
_expenses_stats_controller: ExpensesStatsController | None = None
_payments_controller: PaymentsReconciliationController | None = None
_settings_controller: SettingsController | None = None

_mapper_controller: MapperController | None = None
_sub_category_mapper_controller: SubCategoryMapperController | None = None
_cashflow_mapper_controller: CashflowMapperController | None = None

_reports_cache: list[MonthlyReports] | None = None


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _package_data_dir() -> Path:
    """Return the package data directory (src/budget_analyser/data)."""
    return Path(__file__).resolve().parents[1] / "data"


def _ensure_logger() -> logging.Logger:
    """Create or retrieve the API logger with a rotating file handler."""
    log_dir = _package_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("budget_analyser.api")
    logger.setLevel(logging.INFO)
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        fh = RotatingFileHandler(
            filename=str(log_dir / "api.log"),
            encoding="utf-8",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
        )
        fmt = logging.Formatter(
            fmt=(
                "%(asctime)s | %(levelname).4s | %(name)s "
                "| %(filename)s:%(lineno)d | %(message)s"
            )
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def initialize() -> None:
    """Wire all controllers.

    Must be called exactly once during application startup.
    """
    global \
        _logger, _prefs, _backend_controller, _db_repository, \
        _upload_controller, _budget_goals_controller, \
        _net_worth_controller, _recurring_controller, \
        _savings_controller, _earnings_stats_controller, \
        _expenses_stats_controller, _payments_controller, \
        _settings_controller, _mapper_controller, \
        _sub_category_mapper_controller, \
        _cashflow_mapper_controller, _reports_cache  # noqa: PLW0603

    # Logger
    _logger = _ensure_logger()

    # Settings + preferences
    settings = load_settings()
    _prefs = AppPreferences(settings.ini_config_path)

    try:
        _logger.setLevel(getattr(logging, _prefs.get_log_level()))
    except Exception:  # pylint: disable=broad-exception-caught
        _logger.setLevel(logging.INFO)

    _logger.info("API dependency initialization started")

    # Backend controller (report generation pipeline)
    config = IniAppConfig(path=settings.ini_config_path)
    statement_repo = CsvStatementRepository(
        statement_dir=settings.statement_dir,
        config=config,
        logger=_logger,
    )
    column_mappings = IniColumnMappingProvider(config=config)
    category_mappings = JsonCategoryMappingProvider(
        description_to_sub_category_path=(
            settings.description_to_sub_category_path
        ),
        sub_category_to_category_path=(
            settings.sub_category_to_category_path
        ),
        logger=_logger,
    )
    cashflow_mapping = JsonCashflowMappingProvider(
        cashflow_to_category_path=settings.cashflow_to_category_path,
        logger=_logger,
    )
    report_service = ReportService(
        cashflow_mapping=cashflow_mapping.cashflow_to_category(),
    )
    _backend_controller = BackendController(
        statement_repository=statement_repo,
        column_mappings=column_mappings,
        category_mappings=category_mappings,
        report_service=report_service,
        logger=_logger,
    )

    # Transaction database + repository
    transaction_db = TransactionDatabase(
        db_path=settings.database_path, logger=_logger,
    )
    _db_repository = DatabaseTransactionRepository(
        database=transaction_db, logger=_logger,
    )

    # Ingestion service + upload controller
    category_mapping_provider = JsonCategoryMappingProvider(
        description_to_sub_category_path=(
            settings.description_to_sub_category_path
        ),
        sub_category_to_category_path=(
            settings.sub_category_to_category_path
        ),
        logger=_logger,
    )
    category_mappers = CategoryMappers(
        description_to_sub_category=(
            category_mapping_provider.description_to_sub_category()
        ),
        sub_category_to_category=(
            category_mapping_provider.sub_category_to_category()
        ),
    )
    ingestion_service = TransactionIngestionService(
        database=transaction_db,
        category_mappers=category_mappers,
        logger=_logger,
    )
    _upload_controller = UploadController(
        logger=_logger,
        ini_config=config,
        statements_dir=settings.statement_dir,
        ingestion_service=ingestion_service,
    )

    # Feature repositories
    budget_db_path = settings.database_path.parent / "budget_goals.db"
    budget_goals_repo = BudgetGoalsRepository(
        db_path=budget_db_path, logger=_logger,
    )
    net_worth_repo = NetWorthRepository(
        db_path=budget_db_path, logger=_logger,
    )
    recurring_repo = RecurringRepository(
        db_path=budget_db_path, logger=_logger,
    )

    # Feature controllers
    _budget_goals_controller = BudgetGoalsController(
        repository=budget_goals_repo, logger=_logger,
    )
    _net_worth_controller = NetWorthController(
        repository=net_worth_repo,
    )
    _recurring_controller = RecurringController(
        repository=recurring_repo,
    )
    _savings_controller = SavingsController()
    _settings_controller = SettingsController(_logger, _prefs)

    # Generate initial reports from database (if data exists)
    _regenerate_reports()

    _logger.info("API dependency initialization complete")


# ---------------------------------------------------------------------------
# Report management
# ---------------------------------------------------------------------------

def _regenerate_reports() -> None:
    """Generate reports from the database and wire report-dependent controllers.

    Called during init and after cache invalidation.
    """
    global \
        _reports_cache, _earnings_stats_controller, \
        _expenses_stats_controller, _payments_controller, \
        _mapper_controller, _sub_category_mapper_controller, \
        _cashflow_mapper_controller  # noqa: PLW0603

    assert _db_repository is not None
    assert _backend_controller is not None
    assert _logger is not None

    reports: list[MonthlyReports] = []
    try:
        if _db_repository.has_data():
            transactions = _db_repository.get_processed_transactions()
            reports = _backend_controller.run_from_database(transactions)
            _logger.info(
                "Generated %d monthly reports from database",
                len(reports),
            )
        else:
            _logger.info("No database data; reports list is empty")
    except Exception:  # pylint: disable=broad-exception-caught
        _logger.exception("Error generating reports")

    _reports_cache = reports

    # Wire report-dependent controllers
    settings = load_settings()

    _earnings_stats_controller = EarningsStatsController(
        reports, _logger, budget_controller=_budget_goals_controller,
    )
    _expenses_stats_controller = ExpensesStatsController(
        reports, _logger,
    )
    _payments_controller = PaymentsReconciliationController(
        reports, _logger,
    )

    mapping_store = JsonCategoryMappingStore(
        description_to_sub_category_path=(
            settings.description_to_sub_category_path
        ),
        sub_category_to_category_path=(
            settings.sub_category_to_category_path
        ),
        logger=_logger,
    )
    _mapper_controller = MapperController(reports, _logger, mapping_store)
    _sub_category_mapper_controller = SubCategoryMapperController(
        mapping_store, _logger,
    )

    cashflow_store = JsonCashflowMappingStore(
        cashflow_to_category_path=settings.cashflow_to_category_path,
        logger=_logger,
    )
    _cashflow_mapper_controller = CashflowMapperController(
        cashflow_store, _logger,
    )


def invalidate_reports() -> None:
    """Clear the report cache and regenerate from the database."""
    _regenerate_reports()


# ---------------------------------------------------------------------------
# FastAPI Depends getters
# ---------------------------------------------------------------------------

def get_logger() -> logging.Logger:
    """Return the shared API logger."""
    assert _logger is not None, "Call initialize() first"
    return _logger


def get_prefs() -> AppPreferences:
    """Return the AppPreferences instance."""
    assert _prefs is not None, "Call initialize() first"
    return _prefs


def get_reports() -> list[MonthlyReports]:
    """Return the cached list of MonthlyReports."""
    if _reports_cache is None:
        return []
    return _reports_cache


def get_backend_controller() -> BackendController:
    """Return the BackendController."""
    assert _backend_controller is not None, "Call initialize() first"
    return _backend_controller


def get_db_repository() -> DatabaseTransactionRepository:
    """Return the DatabaseTransactionRepository."""
    assert _db_repository is not None, "Call initialize() first"
    return _db_repository


def get_budget_goals_controller() -> BudgetGoalsController:
    """Return the BudgetGoalsController."""
    assert _budget_goals_controller is not None, "Call initialize() first"
    return _budget_goals_controller


def get_net_worth_controller() -> NetWorthController:
    """Return the NetWorthController."""
    assert _net_worth_controller is not None, "Call initialize() first"
    return _net_worth_controller


def get_recurring_controller() -> RecurringController:
    """Return the RecurringController."""
    assert _recurring_controller is not None, "Call initialize() first"
    return _recurring_controller


def get_savings_controller() -> SavingsController:
    """Return the SavingsController."""
    assert _savings_controller is not None, "Call initialize() first"
    return _savings_controller


def get_earnings_stats_controller() -> EarningsStatsController:
    """Return the EarningsStatsController."""
    assert _earnings_stats_controller is not None, (
        "Call initialize() first"
    )
    return _earnings_stats_controller


def get_expenses_stats_controller() -> ExpensesStatsController:
    """Return the ExpensesStatsController."""
    assert _expenses_stats_controller is not None, (
        "Call initialize() first"
    )
    return _expenses_stats_controller


def get_payments_controller() -> PaymentsReconciliationController:
    """Return the PaymentsReconciliationController."""
    assert _payments_controller is not None, "Call initialize() first"
    return _payments_controller


def get_settings_controller() -> SettingsController:
    """Return the SettingsController."""
    assert _settings_controller is not None, "Call initialize() first"
    return _settings_controller


def get_upload_controller() -> UploadController:
    """Return the UploadController."""
    assert _upload_controller is not None, "Call initialize() first"
    return _upload_controller


def get_mapper_controller() -> MapperController:
    """Return the MapperController."""
    assert _mapper_controller is not None, "Call initialize() first"
    return _mapper_controller


def get_sub_category_mapper_controller() -> SubCategoryMapperController:
    """Return the SubCategoryMapperController."""
    assert _sub_category_mapper_controller is not None, (
        "Call initialize() first"
    )
    return _sub_category_mapper_controller


def get_cashflow_mapper_controller() -> CashflowMapperController:
    """Return the CashflowMapperController."""
    assert _cashflow_mapper_controller is not None, (
        "Call initialize() first"
    )
    return _cashflow_mapper_controller
