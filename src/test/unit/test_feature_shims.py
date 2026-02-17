"""Backward-compatibility shim tests.

Verify that all old import paths still resolve to the new feature
modules and that the classes/functions are identical (same object).
"""

from __future__ import annotations


class TestDomainShims:
    """Tests that old domain imports still work."""

    def test_forecasting_shim(self) -> None:
        from budget_analyser.domain.forecasting import (
            ForecastMethod,
            ForecastPoint,
            ForecastResult,
            ForecastingService,
            forecast_spending,
        )
        from budget_analyser.features.forecasting import (
            ForecastMethod as FM2,
            ForecastingService as FS2,
        )
        assert ForecastMethod is FM2
        assert ForecastingService is FS2

    def test_trend_analysis_shim(self) -> None:
        from budget_analyser.domain.trend_analysis import (
            TrendDirection,
            MonthlyTrend,
            TrendAnalysisResult,
            TrendAnalysisService,
            analyze_spending_trends,
            analyze_income_trends,
        )
        from budget_analyser.features.trends import (
            TrendAnalysisService as TAS2,
        )
        assert TrendAnalysisService is TAS2

    def test_spending_patterns_shim(self) -> None:
        from budget_analyser.domain.spending_patterns import (
            DayOfWeek,
            ParetoItem,
            ParetoAnalysis,
            DayPattern,
            WeeklyPattern,
            Anomaly,
            AnomalyReport,
            SavingsRateTrend,
            SpendingPatternService,
            analyze_spending_patterns,
        )
        from budget_analyser.features.trends import (
            SpendingPatternService as SPS2,
        )
        assert SpendingPatternService is SPS2

    def test_burn_rate_shim(self) -> None:
        from budget_analyser.domain.burn_rate import (
            BurnRateMetrics,
            CategoryBurnRate,
            BurnRateService,
            calculate_burn_rate,
        )
        from budget_analyser.features.trends import (
            BurnRateService as BRS2,
        )
        assert BurnRateService is BRS2

    def test_export_service_shim(self) -> None:
        from budget_analyser.domain.export_service import (
            ExportColumn,
            ExportConfig,
            CsvExporter,
            PdfExporter,
            ExportService,
            format_currency,
            format_percentage,
            EARNINGS_COLUMNS,
            EXPENSES_COLUMNS,
            MONTHLY_SUMMARY_COLUMNS,
            CATEGORY_BREAKDOWN_COLUMNS,
        )
        from budget_analyser.features.export import (
            ExportService as ES2,
        )
        assert ExportService is ES2

    def test_payment_matching_shim(self) -> None:
        from budget_analyser.domain.payment_matching import (
            PaymentPair,
            PaymentMatchResult,
            PaymentMatchingService,
            create_payment_matcher,
        )
        from budget_analyser.features.payments import (
            PaymentMatchingService as PMS2,
        )
        assert PaymentMatchingService is PMS2

    def test_reporting_shim(self) -> None:
        from budget_analyser.domain.reporting import (
            ReportService,
        )
        from budget_analyser.features.reporting import (
            ReportService as RS2,
        )
        assert ReportService is RS2

    def test_categorization_suggestions_shim(self) -> None:
        from budget_analyser.domain.categorization_suggestions import (
            Suggestion,
            SuggestionResult,
            CategorizationSuggestionEngine,
            create_suggestion_engine,
            MERCHANT_PATTERNS,
        )
        from budget_analyser.features.mappers import (
            CategorizationSuggestionEngine as CSE2,
        )
        assert CategorizationSuggestionEngine is CSE2

    def test_transaction_ingestion_shim(self) -> None:
        from budget_analyser.domain.transaction_ingestion import (
            IngestionResult,
            TransactionIngestionService,
        )
        from budget_analyser.features.ingestion import (
            TransactionIngestionService as TIS2,
        )
        assert TransactionIngestionService is TIS2


class TestControllerShims:
    """Tests that old controller imports still work."""

    def test_settings_controller_shim(self) -> None:
        from budget_analyser.controller.settings_controller import (
            SettingsController,
        )
        from budget_analyser.features.settings import (
            SettingsController as SC2,
        )
        assert SettingsController is SC2

    def test_payments_reconciliation_shim(self) -> None:
        from budget_analyser.controller.payments_reconciliation_controller import (  # noqa: E501
            PaymentsReconciliationController,
            PaymentsReconciliationSummary,
        )
        from budget_analyser.features.payments import (
            PaymentsReconciliationController as PRC2,
        )
        assert PaymentsReconciliationController is PRC2

    def test_earnings_stats_shim(self) -> None:
        from budget_analyser.controller.earnings_stats_controller import (
            EarningsStatsController,
            EarningsRow,
        )
        from budget_analyser.features.reporting import (
            EarningsStatsController as ESC2,
        )
        assert EarningsStatsController is ESC2

    def test_expenses_stats_shim(self) -> None:
        from budget_analyser.controller.expenses_stats_controller import (
            ExpensesStatsController,
        )
        from budget_analyser.features.reporting import (
            ExpensesStatsController as ESC2,
        )
        assert ExpensesStatsController is ESC2

    def test_mapper_controller_shim(self) -> None:
        from budget_analyser.controller.mapper_controller import (
            MapperController,
        )
        from budget_analyser.features.mappers import (
            MapperController as MC2,
        )
        assert MapperController is MC2

    def test_cashflow_mapper_shim(self) -> None:
        from budget_analyser.controller.cashflow_mapper_controller import (
            CashflowMapperController,
        )
        from budget_analyser.features.mappers import (
            CashflowMapperController as CMC2,
        )
        assert CashflowMapperController is CMC2

    def test_sub_category_mapper_shim(self) -> None:
        from budget_analyser.controller.sub_category_mapper_controller import (  # noqa: E501
            SubCategoryMapperController,
        )
        from budget_analyser.features.mappers import (
            SubCategoryMapperController as SCMC2,
        )
        assert SubCategoryMapperController is SCMC2

    def test_upload_controller_shim(self) -> None:
        from budget_analyser.controller.upload_controller import (
            UploadController,
            UploadResult,
        )
        from budget_analyser.features.ingestion import (
            UploadController as UC2,
        )
        assert UploadController is UC2


class TestControllerPackageInit:
    """Tests that controller/__init__.py package re-exports work."""

    def test_controller_package_exports(self) -> None:
        from budget_analyser.controller import (
            SettingsController,
            EarningsStatsController,
            ExpensesStatsController,
            PaymentsReconciliationController,
            MapperController,
            CashflowMapperController,
            SubCategoryMapperController,
            UploadController,
        )
        # All imports should succeed (no ImportError)
        assert SettingsController is not None
        assert UploadController is not None
