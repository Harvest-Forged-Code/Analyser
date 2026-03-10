"""Dependency wiring for the FastAPI layer.

Composition root: every feature service is available as a
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
from budget_analyser.settings.ini_config import IniAppConfig
from budget_analyser.features.ingestion.models import (
    IniColumnMappingProvider,
    CsvStatementRepository,
)
from budget_analyser.features.mappers.models import (
    JsonCategoryMappingProvider,
    JsonCashflowMappingProvider,
    JsonCategoryMappingStore,
    JsonCashflowMappingStore,
)
from budget_analyser.core.database import (
    TransactionDatabase,
    DatabaseTransactionRepository,
)
from budget_analyser.features.reporting.service import (
    ReportService,
    ReportPipelineService as BackendController,
)
from budget_analyser.features.budget_goals.models import (
    BudgetGoalsModel,
)
from budget_analyser.features.budget_goals.service import (
    BudgetGoalsService,
)
from budget_analyser.features.savings.service import SavingsService
from budget_analyser.features.ingestion.service import (
    TransactionIngestionService,
    UploadService,
)
from budget_analyser.features.ingestion.models import (
    UploadHistoryModel,
)
from budget_analyser.features.mappers.service import (
    MapperService,
)
from budget_analyser.features.mappers.cashflow_service import (
    CashflowMapperService,
)
from budget_analyser.features.mappers.sub_category_service import (
    SubCategoryMapperService,
)
from budget_analyser.features.settings.service import SettingsService
from budget_analyser.features.reporting.earnings_service import (
    EarningsStatsService,
)
from budget_analyser.features.reporting.expenses_service import (
    ExpensesStatsService,
)
from budget_analyser.features.recategorize.service import (
    RecategorizeService,
    RecategorizeOrchestrator,
)
from budget_analyser.features.ingestion.categorization import CategoryMappers
from budget_analyser.features.auto_update.service import AutoUpdateService
from budget_analyser.features.payments.service import (
    PaymentReconciliationService,
)
from budget_analyser.features.recurring.models import RecurringModel
from budget_analyser.features.recurring.service import (
    RecurringAnalyticsService,
)
from budget_analyser.version import get_version

# ---------------------------------------------------------------------------
# Module-level singletons (set by ``initialize()``)
# ---------------------------------------------------------------------------
# pylint: disable=invalid-name
_logger: logging.Logger | None = None
_prefs: AppPreferences | None = None
_backend_controller: BackendController | None = None
_db_repository: DatabaseTransactionRepository | None = None
_upload_service: UploadService | None = None

_budget_goals_service: BudgetGoalsService | None = None
_savings_service: SavingsService | None = None
_earnings_stats_service: EarningsStatsService | None = None
_expenses_stats_service: ExpensesStatsService | None = None
_settings_service: SettingsService | None = None

_mapper_service: MapperService | None = None
_sub_category_mapper_service: SubCategoryMapperService | None = None
_cashflow_mapper_service: CashflowMapperService | None = None
_recategorize_service: RecategorizeOrchestrator | None = None
_transaction_db: TransactionDatabase | None = None
_auto_update_service: AutoUpdateService | None = None
_payment_reconciliation_service: PaymentReconciliationService | None = None
_recurring_analytics_service: RecurringAnalyticsService | None = None

_reports_cache: list[MonthlyReports] | None = None
# pylint: enable=invalid-name


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

def initialize() -> None:  # pylint: disable=too-many-locals
    """Wire all services.

    Must be called exactly once during application startup.

    Raises:
        FileNotFoundError: If required config or mapping files are
            missing from the data directory.
        DataSourceError: If JSON mapping files contain invalid data.
    """
    # pylint: disable=global-statement
    global \
        _logger, _prefs, _backend_controller, _db_repository, \
        _upload_service, _budget_goals_service, \
        _savings_service, _settings_service, \
        _recategorize_service, _transaction_db, \
        _auto_update_service, \
        _payment_reconciliation_service, \
        _recurring_analytics_service  # noqa: PLW0603
    # pylint: enable=global-statement

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
    _transaction_db = transaction_db
    _db_repository = DatabaseTransactionRepository(
        database=transaction_db, logger=_logger,
    )

    # Ingestion service + upload service
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
        ini_config=config,
        logger=_logger,
    )
    # Recategorize orchestrator
    recategorize_svc = RecategorizeService(
        category_mappers=category_mappers, logger=_logger,
    )
    _recategorize_service = RecategorizeOrchestrator(
        database=transaction_db,
        service=recategorize_svc,
        logger=_logger,
    )

    # Feature models
    budget_db_path = settings.database_path.parent / "budget_goals.db"
    upload_history_model = UploadHistoryModel(
        db_path=budget_db_path, logger=_logger,
    )
    _upload_service = UploadService(
        logger=_logger,
        ini_config=config,
        statements_dir=settings.statement_dir,
        ingestion_service=ingestion_service,
        upload_history_repo=upload_history_model,
    )
    budget_goals_model = BudgetGoalsModel(
        db_path=budget_db_path, logger=_logger,
    )

    # Feature services
    _budget_goals_service = BudgetGoalsService(
        model=budget_goals_model, logger=_logger,
    )
    _savings_service = SavingsService()
    _settings_service = SettingsService(_logger, _prefs)

    # Payment reconciliation service
    _payment_reconciliation_service = PaymentReconciliationService(
        db_path=settings.database_path, logger=_logger,
    )

    # Recurring analytics service
    recurring_model = RecurringModel(
        db_path=budget_db_path, logger=_logger,
    )
    _recurring_analytics_service = RecurringAnalyticsService(
        model=recurring_model,
        db_path=settings.database_path,
        logger=_logger,
    )

    # Auto-update service
    _auto_update_service = AutoUpdateService(
        github_owner="Harvest-Forged-Code",
        github_repo="Analyser",
        current_version=get_version(),
        logger=_logger,
    )

    # Generate initial reports from database (if data exists)
    _regenerate_reports()

    _logger.info("API dependency initialization complete")


# ---------------------------------------------------------------------------
# Report management
# ---------------------------------------------------------------------------

def _regenerate_reports() -> None:
    """Generate reports from the database and wire report-dependent services.

    Called during init and after cache invalidation.
    """
    # pylint: disable=global-statement
    global \
        _reports_cache, _earnings_stats_service, \
        _expenses_stats_service, _mapper_service, \
        _sub_category_mapper_service, \
        _cashflow_mapper_service, _recategorize_service  # noqa: PLW0603
    # pylint: enable=global-statement

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

    # Wire report-dependent services
    settings = load_settings()

    _earnings_stats_service = EarningsStatsService(
        reports, _logger, budget_controller=_budget_goals_service,
    )
    _expenses_stats_service = ExpensesStatsService(
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
    _mapper_service = MapperService(reports, _logger, mapping_store)
    _sub_category_mapper_service = SubCategoryMapperService(
        mapping_store, _logger,
    )

    cashflow_store = JsonCashflowMappingStore(
        cashflow_to_category_path=settings.cashflow_to_category_path,
        logger=_logger,
    )
    _cashflow_mapper_service = CashflowMapperService(
        cashflow_store, _logger,
    )

    # Rebuild recategorize service so it uses the freshly loaded mappers
    if _transaction_db is not None:
        fresh_category_mappers = CategoryMappers(
            description_to_sub_category=mapping_store.load_desc_to_sub(),
            sub_category_to_category=mapping_store.load_sub_to_cat(),
        )
        _recategorize_service = RecategorizeOrchestrator(
            database=_transaction_db,
            service=RecategorizeService(
                category_mappers=fresh_category_mappers, logger=_logger,
            ),
            logger=_logger,
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


def get_budget_goals_service() -> BudgetGoalsService:
    """Return the BudgetGoalsService."""
    assert _budget_goals_service is not None, "Call initialize() first"
    return _budget_goals_service


def get_savings_service() -> SavingsService:
    """Return the SavingsService."""
    assert _savings_service is not None, "Call initialize() first"
    return _savings_service


def get_earnings_stats_service() -> EarningsStatsService:
    """Return the EarningsStatsService."""
    assert _earnings_stats_service is not None, (
        "Call initialize() first"
    )
    return _earnings_stats_service


def get_expenses_stats_service() -> ExpensesStatsService:
    """Return the ExpensesStatsService."""
    assert _expenses_stats_service is not None, (
        "Call initialize() first"
    )
    return _expenses_stats_service


def get_settings_service() -> SettingsService:
    """Return the SettingsService."""
    assert _settings_service is not None, "Call initialize() first"
    return _settings_service


def get_upload_service() -> UploadService:
    """Return the UploadService."""
    assert _upload_service is not None, "Call initialize() first"
    return _upload_service


def get_mapper_service() -> MapperService:
    """Return the MapperService."""
    assert _mapper_service is not None, "Call initialize() first"
    return _mapper_service


def get_sub_category_mapper_service() -> SubCategoryMapperService:
    """Return the SubCategoryMapperService."""
    assert _sub_category_mapper_service is not None, (
        "Call initialize() first"
    )
    return _sub_category_mapper_service


def get_cashflow_mapper_service() -> CashflowMapperService:
    """Return the CashflowMapperService."""
    assert _cashflow_mapper_service is not None, (
        "Call initialize() first"
    )
    return _cashflow_mapper_service


def get_recategorize_service() -> RecategorizeOrchestrator:
    """Return the RecategorizeOrchestrator."""
    assert _recategorize_service is not None, (
        "Call initialize() first"
    )
    return _recategorize_service


def get_payment_reconciliation_service() -> PaymentReconciliationService:
    """Return the PaymentReconciliationService."""
    assert _payment_reconciliation_service is not None, (
        "Call initialize() first"
    )
    return _payment_reconciliation_service


def get_recurring_analytics_service() -> RecurringAnalyticsService:
    """Return the RecurringAnalyticsService."""
    assert _recurring_analytics_service is not None, (
        "Call initialize() first"
    )
    return _recurring_analytics_service


def get_auto_update_service() -> AutoUpdateService:
    """Return the AutoUpdateService."""
    assert _auto_update_service is not None, "Call initialize() first"
    return _auto_update_service


# ---------------------------------------------------------------------------
# Backward compatibility aliases
# ---------------------------------------------------------------------------
get_budget_goals_controller = get_budget_goals_service
get_savings_controller = get_savings_service
get_earnings_stats_controller = get_earnings_stats_service
get_expenses_stats_controller = get_expenses_stats_service
get_settings_controller = get_settings_service
get_upload_controller = get_upload_service
get_mapper_controller = get_mapper_service
get_sub_category_mapper_controller = get_sub_category_mapper_service
get_cashflow_mapper_controller = get_cashflow_mapper_service
get_recategorize_controller = get_recategorize_service
