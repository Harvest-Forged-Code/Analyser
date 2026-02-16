# High-Level Design (HLD) - Budget Analyser

## 1. System Overview

**Budget Analyser** is a cross-platform desktop application for personal finance tracking and analysis. It processes bank statement CSV files, categorizes transactions using keyword mappings, stores them in SQLite, and generates comprehensive financial reports through an intuitive PySide6 GUI with light/dark themes.

### Primary Goals

- Ingest bank statements from multiple sources (Chase, Citi, Discover, Bilt)
- Automatically categorize transactions using configurable keyword mappings with scored matching
- Generate monthly and yearly financial reports with hierarchical category breakdowns
- Support budget goal setting and expense/earnings tracking
- Track recurring transactions, savings, and net worth
- Provide advanced analytics: forecasting, trend analysis, burn rate, spending patterns, anomaly detection
- Export reports in multiple formats (CSV, Excel, PDF)
- Provide an intuitive GUI with 12 specialized pages

### Target Users

Individual users who want to:
- Consolidate statements from multiple bank accounts
- Understand spending patterns across categories
- Set and track budget/earnings goals
- Monitor net worth and savings rate over time
- Forecast future expenses and detect anomalies

---

## 2. Architecture Overview

The application follows a **Hybrid Architecture**: a horizontal layered foundation combined with **vertical feature slices** for cohesive feature modules. Migrated features (starting with `budget_goals`) own all their layers in a single directory, while unmigrated features still span the traditional horizontal layers.

```mermaid
flowchart TB
    subgraph Presentation["PRESENTATION LAYER"]
        direction LR
        Login["LoginWindow<br/>(Authentication)"]
        Dashboard["DashboardWindow<br/>(Shell + Navigation)"]
        Pages["12 Pages<br/>(Reports, Goals, Data, Settings)"]
        Widgets["Reusable Widgets<br/>(KPI, Charts, Filters, Progress)"]
    end

    subgraph Features["FEATURE SLICES (vertical)"]
        direction LR
        BG["budget_goals/<br/>controller + service +<br/>repository + models + page"]
        Future["net_worth/ recurring/<br/>savings/ ... (planned)"]
    end

    subgraph Core["CORE (shared foundation)"]
        direction LR
        CoreProto["protocols.py"]
        CoreErr["errors.py"]
        CoreDB["database.py"]
        CoreModels["models.py<br/>(MonthlyReports)"]
    end

    subgraph Controller["CONTROLLER LAYER (legacy)"]
        direction LR
        Backend["BackendController"]
        Upload["UploadController"]
        Mapper["MapperControllers<br/>(3 types)"]
        BudgetCtrl["BudgetController<br/>(facade shim)"]
        Stats["StatsControllers<br/>(Earnings, Expenses, Yearly, Dashboard)"]
        SettingsCtrl["SettingsController"]
    end

    subgraph Domain["DOMAIN LAYER (legacy)"]
        direction LR
        Processor["TransactionProcessor"]
        Reporter["ReportService"]
        Formatters["StatementFormatters<br/>(Factory + Strategy)"]
        Ingestion["IngestionService"]
        Analytics["Analytics Services<br/>(Forecasting, Trends,<br/>BurnRate, Patterns,<br/>Matching, Export)"]
    end

    subgraph Infrastructure["INFRASTRUCTURE LAYER"]
        direction LR
        TxDB[("TransactionDB<br/>(SQLite)")]
        BudgetDB[("BudgetDB<br/>(legacy, shrinking)")]
        CSV["CsvStatementRepository"]
        JSON["JsonMappingProviders<br/>(3 types)"]
        INI["IniAppConfig"]
    end

    Presentation --> Features
    Presentation --> Controller
    Features --> Core
    Controller --> Domain
    Domain -.->|depends on protocols only| Infrastructure
    Features -.->|uses shared DB| Core
    BudgetCtrl -.->|delegates to| BG
```

### Dependency Rule

Each layer depends only on the layer directly below it. The domain layer defines **Protocol interfaces** that the infrastructure layer implements. Feature slices depend on the shared `core/` module but not on each other.

```mermaid
flowchart LR
    subgraph Core
        P[Protocols + Errors<br/>+ Database + Models]
    end
    subgraph Features
        FS[Feature Slices<br/>budget_goals/...]
    end
    subgraph Domain
        D[Legacy Domain Services]
    end
    subgraph Infrastructure
        Impl[Implementations]
    end
    subgraph Views
        V[Composition Root<br/>app_gui.py]
    end

    V -->|creates & injects| Impl
    V -->|creates & injects| FS
    FS -->|depends on| P
    D -.->|depends on| P
    Impl -.->|implements| P
```

### Migration Strategy

Features are incrementally migrated from horizontal layers to vertical slices:

```mermaid
flowchart LR
    subgraph Before["Horizontal Layers"]
        C["controller/<br/>budget_controller.py"]
        D["domain/<br/>(business logic)"]
        I["infrastructure/<br/>budget_database.py"]
        VP["views/pages/<br/>budget_goals_page.py"]
    end

    subgraph After["Vertical Slice"]
        F["features/budget_goals/<br/>controller.py<br/>service.py<br/>repository.py<br/>models.py<br/>page.py"]
    end

    Before -->|"migrate + shim"| After
```

During migration, backward-compatibility shims in old locations re-export from the new feature module, so existing consumers continue to work.

---

## 3. Design Patterns

| Pattern | Usage | Example |
|---------|-------|---------|
| **Vertical Slice** | Each feature owns all layers (model, repo, service, controller, page) | `features/budget_goals/` (pilot), future: net_worth, recurring, savings |
| **Layered Architecture** | Separates presentation, application, domain, and infrastructure | 4-layer structure (legacy, being migrated to slices) |
| **Dependency Injection** | Controllers receive dependencies through constructor injection | `BackendController.__init__(*, statement_repository, ...)` |
| **Protocol/Interface** | Core defines stable interfaces; infrastructure implements | `StatementRepository`, `ColumnMappingProvider`, `CategoryMappingProvider` |
| **Strategy** | Bank-specific statement formatters with different algorithms | `CitiStatementFormatter`, `DiscoverStatementFormatter`, `DefaultStatementFormatter` |
| **Factory** | `create_statement_formatter()` selects formatter by account | Returns appropriate strategy based on account name |
| **Repository** | Database and CSV repositories abstract data access | `BudgetGoalsRepository`, `CsvStatementRepository`, `DatabaseTransactionRepository` |
| **Service Layer** | Pure business logic functions with no infrastructure deps | `budget_goals.service`, `ReportService`, `TransactionProcessor` |
| **Observer** | Qt Signal/Slot for event-driven UI communication | `upload_successful`, `refresh_requested`, `reload_requested` |
| **Template Method** | Base formatter defines steps; subclasses override hooks | `BaseStatementFormatter._bank_specific_formatting()` |
| **Data Transfer Object** | Immutable frozen dataclasses pass data across layers | `MonthlyReports`, `BudgetGoal`, `IngestionResult` |
| **Mixin** | Reusable UI utilities for consistent page styling | `ModernPageMixin` |
| **Composition Root** | Single location wires all dependencies | `app_gui.py::_build_controller()` |

---

## 4. Major Components

### 4.1 Core Module (`core/`)

Shared foundations that all feature slices and legacy layers depend on:

| Module | Responsibility |
|--------|----------------|
| `protocols.py` | Domain interfaces: `StatementRepository`, `ColumnMappingProvider`, `CategoryMappingProvider` |
| `errors.py` | Domain exception hierarchy: `DomainError`, `ValidationError`, `MappingNotFoundError`, `DataSourceError` |
| `database.py` | Shared SQLite connection factory (`get_connection()`) used by all feature repositories |
| `models.py` | Cross-feature DTOs: `MonthlyReports` (frozen dataclass consumed by many pages) |

### 4.2 Feature Slices (`features/`)

Self-contained vertical slices where each feature owns all its layers:

#### `features/budget_goals/` (Pilot - Complete)

| Module | Responsibility |
|--------|----------------|
| `models.py` | `BudgetGoal`, `EarningsGoal`, `BudgetProgress` DTOs |
| `repository.py` | `BudgetGoalsRepository` — SQLite CRUD for budget_goals and earnings_goals tables |
| `service.py` | Pure business logic: `calculate_budget_progress()`, `build_earnings_goal_map()` |
| `controller.py` | `BudgetGoalsController` — thin facade delegating to repository + service |
| `page.py` | `BudgetGoalsPage` — Qt widget with Set Goals and Manage Goals tabs |

#### Planned Feature Slices (Phase 3)

| Feature | Status | Key Responsibilities |
|---------|--------|----------------------|
| `net_worth/` | Planned | Account management, net worth calculation |
| `recurring/` | Planned | Recurring transaction detection and tracking |
| `savings/` | Planned | Savings rate metrics and monthly breakdown |
| `ingestion/` | Planned | CSV import pipeline |
| `mappers/` | Planned | Category mapping CRUD |
| `reporting/` | Planned | Earnings and expenses report generation |
| `payments/` | Planned | Payment reconciliation |
| `forecasting/` | Planned | Time-series expense forecasting |
| `trends/` | Planned | Trend analysis and spending patterns |
| `export/` | Planned | CSV/Excel/PDF export |
| `settings/` | Planned | Application preferences |

### 4.3 Presentation Layer (`views/`)

| Component | Responsibility |
|-----------|----------------|
| `app_gui.py` | Composition root; logging setup; dependency wiring; launches Qt application |
| `login_window.py` | Password-protected authentication with SHA-256 salted hashing |
| `dashboard_window.py` | Main shell with header bar, collapsible sidebar navigation, stacked page container |
| `pages/` (12 pages) | Specialized pages for reports, goals, data management, settings |
| `widgets/` (8+ files) | Reusable UI components: KPI cards, charts, filters, progress bars, empty states, goal cards |
| `styles.py` | Theme management (light/dark), QSS stylesheets |

### 4.4 Controller Layer (`controller/` — legacy, being migrated)

| Controller | Responsibility | Migration Status |
|------------|----------------|------------------|
| `BackendController` | Orchestrates load -> format -> process -> report pipeline | Stays (cross-cutting) |
| `UploadController` | Validates and processes uploaded CSV files with ingestion | Planned: `features/ingestion/` |
| `MapperController` | Manages description -> sub_category keyword mappings | Planned: `features/mappers/` |
| `SubCategoryMapperController` | Manages sub_category -> category mappings | Planned: `features/mappers/` |
| `CashflowMapperController` | Manages category -> earnings/expenses classification | Planned: `features/mappers/` |
| `BudgetController` | **Backward-compat facade** — delegates budget/earnings goals to `features/budget_goals`; retains savings, net worth, recurring until migrated | Partially migrated |
| `ExpensesStatsController` | Generates expense reports, category nodes, pivots | Planned: `features/reporting/` |
| `EarningsStatsController` | Generates earnings reports and breakdowns | Planned: `features/reporting/` |
| `YearlySummaryStatsController` | Year-over-year aggregations | Planned: `features/reporting/` |
| `CashflowDashboardController` | Cashflow dashboard KPIs and charts | Planned: `features/reporting/` |
| `SettingsController` | Application preferences management | Planned: `features/settings/` |

### 4.5 Domain Layer (`domain/` — legacy, being migrated)

| Service | Responsibility |
|---------|----------------|
| `TransactionProcessor` | Applies scored keyword matching to categorize transactions |
| `TransactionIngestionService` | End-to-end CSV ingestion pipeline (load -> format -> process -> persist) |
| `ReportService` | Generates earnings/expenses/category reports with pivoting |
| `StatementFormatters` | Normalize bank CSVs to canonical schema (Factory + Strategy) |
| `CategoryMappers` | Immutable container for keyword mappings |
| `KeywordMatching` | Scored substring/exact matching with position and weight bonuses |
| `Forecasting` | Predict future expenses using linear regression with ensemble methods |
| `TrendAnalysis` | Month-over-month, year-over-year trend analysis with volatility |
| `BurnRate` | Calculate spending velocity, projections, and budget warnings |
| `SpendingPatterns` | Pareto analysis, weekly patterns, anomaly detection (Z-score) |
| `PaymentMatching` | Reconcile payment pairs with confidence scoring |
| `CategorizationSuggestions` | Suggest categories for unmapped transactions |
| `ExportService` | Export reports to CSV/Excel/PDF formats |

> **Note:** `Protocols` and `Errors` have moved to `core/`. Old `domain/protocols.py` and `domain/errors.py` are backward-compatibility shims that re-export from `core/`.

### 4.6 Infrastructure Layer (`infrastructure/`)

| Adapter | Responsibility |
|---------|----------------|
| `TransactionDatabase` | SQLite persistence for processed transactions with duplicate prevention |
| `DatabaseTransactionRepository` | Read-only adapter for loading transactions for reports |
| `BudgetDatabase` | SQLite persistence for accounts, recurring (budget/earnings goals migrated to `features/budget_goals/repository.py`) |
| `CsvStatementRepository` | Loads CSV files from filesystem (UTF-8 BOM handling) |
| `IniAppConfig` | Reads INI configuration (accounts, column mappings) |
| `IniColumnMappingProvider` | Per-account column mapping adapter |
| `JsonCategoryMappingProvider` | Loads keyword mappings from JSON files |
| `JsonCategoryMappingStore` | Loads and atomically saves keyword mappings |
| `JsonCashflowMappingProvider` | Loads earnings/expenses classification |
| `JsonCashflowMappingStore` | Loads and atomically saves cashflow mappings |

---

## 5. Application Flow

### 5.1 Startup and Authentication Flow

```mermaid
flowchart TD
    Start([python -m budget_analyser]) --> LoadSettings["Load Settings<br/>(env vars, .env, defaults)"]
    LoadSettings --> LoadPrefs["Load Preferences<br/>(theme, log level, password)"]
    LoadPrefs --> SetupLogger["Setup Logger<br/>(5MB rotating, 3 backups)"]
    SetupLogger --> CreateApp["Create QApplication<br/>+ Apply Theme"]
    CreateApp --> BuildCtrl["Build BackendController<br/>(dependency injection)"]
    BuildCtrl --> ShowLogin["Show LoginWindow"]

    ShowLogin --> VerifyPwd{Password<br/>Correct?}
    VerifyPwd -->|No| ShowLogin
    VerifyPwd -->|Yes| CheckData

    subgraph CheckData["Data Availability Check"]
        C1{DB has<br/>data?}
        C2{CSVs<br/>present?}
        RestrictedMode["Restricted Mode<br/>(Upload + Settings only)"]
        IngestCSVs["Ingest CSVs<br/>to Database"]
        LoadFromDB["Load Transactions<br/>from Database"]
    end

    C1 -->|Yes| LoadFromDB
    C1 -->|No| C2
    C2 -->|Yes| IngestCSVs
    C2 -->|No| RestrictedMode
    IngestCSVs --> LoadFromDB

    LoadFromDB --> GenReports["Generate MonthlyReports<br/>via BackendController"]
    GenReports --> OpenDash["Open DashboardWindow<br/>(all pages enabled)"]
    RestrictedMode --> OpenDashRestricted["Open DashboardWindow<br/>(restricted mode)"]
```

### 5.2 CSV Ingestion Pipeline

```mermaid
flowchart TD
    Upload["User Uploads CSV<br/>via UploadPage"] --> Validate["Validate CSV Format<br/>(UploadController)"]

    Validate -->|Invalid| ShowError["Show Error Message"]
    Validate -->|Valid| CopyFile["Copy to statements/ dir"]

    CopyFile --> LoadCSV["Load CSV<br/>(pd.read_csv, utf-8-sig)"]
    LoadCSV --> SelectFormatter["Select Formatter<br/>(Factory Pattern)"]

    subgraph FormatStep["Bank-Specific Formatting"]
        F1["Ensure 'amount' column<br/>(derive from Debit/Credit)"]
        F2["Rename columns<br/>(INI mapping)"]
        F3["Add 'from_account' column"]
        F4["Keep REQUIRED_COLUMNS only"]
        F5["Apply bank-specific logic<br/>(e.g., Citi inverts signs)"]
        F6["Parse transaction_date<br/>as datetime"]
        F1 --> F2 --> F3 --> F4 --> F5 --> F6
    end

    SelectFormatter --> FormatStep

    F6 --> Categorize

    subgraph Categorize["Transaction Categorization"]
        Cat1["Pass 1: description -> sub_category<br/>(scored substring matching)"]
        Cat2["Pass 2: sub_category -> category<br/>(scored exact matching)"]
        Cat3["Pass 3: amount -> c_or_d<br/>(positive=earnings, negative=expenditures)"]
        Cat1 --> Cat2 --> Cat3
    end

    Cat3 --> Persist["INSERT OR IGNORE<br/>into SQLite<br/>(deduplicated)"]
    Persist --> EmitSignal["Emit upload_successful<br/>signal"]
    EmitSignal --> ReloadDash["Reload Dashboard<br/>with new reports"]
```

### 5.3 Report Generation Pipeline

```mermaid
flowchart TD
    Trigger["Trigger: App Start / Upload / Mapping Saved"]
    Trigger --> LoadTx["Load all transactions<br/>from TransactionDatabase"]
    LoadTx --> GroupMonth["Group by year_month<br/>(YYYY-MM periods)"]

    GroupMonth --> GenReports

    subgraph GenReports["For Each Month"]
        RE["Filter Earnings<br/>(category in EARNINGS_CATEGORIES<br/>& amount > 0)"]
        RX["Filter Expenses<br/>(category in EXPENSE_CATEGORIES<br/>| amount < 0)"]
        PC["Pivot: Category x Month<br/>(sum of amounts)"]
        PS["Pivot: Sub-Category x Month<br/>(sum of amounts)"]
        MR["Create MonthlyReports<br/>(frozen dataclass)"]

        RE --> MR
        RX --> MR
        PC --> MR
        PS --> MR
    end

    MR --> ReturnList["Return List of MonthlyReports"]
    ReturnList --> UpdatePages["Update Dashboard Pages<br/>with new data"]
```

### 5.4 Mapping Refresh Flow

```mermaid
flowchart TD
    UserSaves["User saves mappings<br/>in MapperPage"] --> EmitRefresh["Emit refresh_requested<br/>signal"]
    EmitRefresh --> StartWorker["Start ReportRefreshWorker<br/>(QThread)"]
    StartWorker --> ShowProgress["Show Progress Dialog"]

    subgraph WorkerThread["Background Worker Thread"]
        W1["Step 1: Reload Mappers<br/>(re-read JSON files)"]
        W2["Step 2: Rebuild Reports<br/>(BackendController.run_from_database)"]
        W3["Step 3: Finalize"]
        W1 --> W2 --> W3
    end

    ShowProgress --> WorkerThread
    W3 -->|Success| RebuildPages["Replace Dashboard Pages<br/>with updated data"]
    W3 -->|Error| ShowError["Show Error Dialog"]
```

---

## 6. Dashboard Architecture

### 6.1 Navigation Structure

```mermaid
flowchart LR
    subgraph Sidebar["Sidebar Navigation"]
        direction TB
        G1["REPORTS"]
        P0["Cashflow Dashboard"]
        P1["Yearly Summary"]
        P2["Earnings"]
        P3["Expenses"]
        P4["Payments"]

        G2["GOALS"]
        P5["Budget Goals"]
        P6["Savings"]
        P7["Net Worth"]

        G3["AUTOMATION"]
        P8["Recurring"]

        G4["DATA"]
        P9["Upload"]
        P10["Mapper Hub"]

        G5["CONFIGURATION"]
        P11["Settings"]

        G1 --- P0 --- P1 --- P2 --- P3 --- P4
        G2 --- P5 --- P6 --- P7
        G3 --- P8
        G4 --- P9 --- P10
        G5 --- P11
    end

    subgraph Content["Stacked Widget (12 pages)"]
        SW["Active Page Content"]
    end

    Sidebar -->|Navigate| Content
```

### 6.2 Page-Controller-Domain Mapping

| Page (Index) | Controller | Services / Repository | Module |
|---|---|---|---|
| Cashflow Dashboard (0) | CashflowDashboardController | ReportService, BurnRate | `controller/` (legacy) |
| Yearly Summary (1) | YearlySummaryStatsController | ReportService | `controller/` (legacy) |
| Earnings (2) | EarningsStatsController | ReportService, BudgetGoalsController | `controller/` (legacy) |
| Expenses (3) | ExpensesStatsController | ReportService, BudgetGoalsController | `controller/` (legacy) |
| Payments (4) | - (direct data) | PaymentMatching | `domain/` (legacy) |
| Budget Goals (5) | **BudgetGoalsController** | **BudgetGoalsRepository, service** | **`features/budget_goals/`** |
| Savings (6) | BudgetController | BudgetDatabase | `controller/` (legacy) |
| Net Worth (7) | BudgetController | BudgetDatabase | `controller/` (legacy) |
| Recurring (8) | BudgetController | BudgetDatabase | `controller/` (legacy) |
| Upload (9) | UploadController | TransactionIngestionService | `controller/` (legacy) |
| Mapper Hub (10) | MapperController + 2 sub-controllers | JsonMappingStores | `controller/` (legacy) |
| Settings (11) | SettingsController | AppPreferences | `controller/` (legacy) |

---

## 7. Signal/Event Architecture

```mermaid
sequenceDiagram
    participant U as User
    participant UP as UploadPage
    participant DW as DashboardWindow
    participant AG as app_gui.py
    participant BC as BackendController
    participant DB as TransactionDB

    Note over U,DB: Upload Flow
    U->>UP: Upload CSV file
    UP->>UP: Validate & Ingest
    UP-->>DW: upload_successful signal
    DW-->>AG: reload_requested signal
    AG->>DB: Load transactions
    AG->>BC: run_from_database()
    BC-->>AG: List[MonthlyReports]
    AG->>DW: Rebuild pages with reports
    AG->>DW: enable_all_pages()

    Note over U,DB: Mapping Refresh Flow
    U->>DW: Save mappings in MapperPage
    DW->>DW: _on_mapping_saved()
    DW->>DW: Start ReportRefreshWorker (QThread)
    DW->>BC: Reload mappers + Rebuild reports
    BC-->>DW: New MonthlyReports
    DW->>DW: _rebuild_pages(reports)

    Note over U,DB: Theme Toggle Flow
    U->>DW: Click theme toggle
    DW->>DW: Toggle prefs.theme (dark/light)
    DW->>DW: Update QSS stylesheet
    DW->>DW: Refresh all nav icons
```

---

## 8. Technology Stack

| Layer | Technology |
|-------|------------|
| **Presentation** | PySide6 (Qt 6), QSS stylesheets, qtawesome icons, pyqtgraph charts |
| **Application** | Python 3.11+ (pure Python controllers) |
| **Domain Logic** | Pure Python, pandas DataFrames, numpy (numerical) |
| **Database** | SQLite (file-based, two databases) |
| **Configuration** | INI files, JSON files, Environment variables, `.env` file |
| **Build** | setuptools, PyInstaller |
| **Testing** | pytest, pytest-qt (optional) |
| **Linting** | pylint (100 char line limit, strict design limits) |
| **CI/CD** | GitHub Actions (test matrix, pylint, multi-platform release) |
| **Version Control** | Git with tag-based semantic versioning |

---

## 9. External Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PySide6 | ~6.8.2 | Qt GUI framework |
| pandas | ~2.3.3 | DataFrame operations and data analysis |
| numpy | ~2.2.3 | Numerical computing (statistics, forecasting) |
| pyqtgraph | ~0.13.7 | Interactive chart widgets |
| qtawesome | ~1.3.0 | Icon library for navigation and UI |
| sqlite3 | stdlib | Persistent storage |
| configparser | stdlib | INI file parsing |
| json | stdlib | Mapping file I/O |
| logging | stdlib | Application diagnostics |

### Build & Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PyInstaller | 6.0+ | Executable bundling (Windows/macOS) |
| pytest | ~8.3.4 | Testing framework |
| pylint | - | Code linting |
| pip | ~25.3 | Package manager |
| wheel | ~0.41.2 | Wheel format support |
| setuptools | ~44.1.1 | Build system |

---

## 10. Deployment Model

### Development Mode

```bash
python -m budget_analyser
```

- Data stored in `src/budget_analyser/data/`
- Configuration via environment variables or `.env` file
- Logs to `data/logs/gui_app.log` (5MB rotating, 3 backups)

### Production Mode (Bundled Executable)

```mermaid
flowchart LR
    subgraph CI["GitHub Actions CI/CD"]
        Tag["Auto Version Tag<br/>(patch increment)"]
        WinBuild["PyInstaller<br/>Windows .exe"]
        MacIntel["PyInstaller<br/>macOS Intel"]
        MacARM["PyInstaller<br/>macOS Apple Silicon"]
        Release["GitHub Release<br/>with all artifacts"]
    end

    Tag --> WinBuild
    Tag --> MacIntel
    Tag --> MacARM
    WinBuild --> Release
    MacIntel --> Release
    MacARM --> Release
```

- PyInstaller creates standalone `.app` (macOS) or `.exe` (Windows)
- Includes Python runtime, all dependencies, and bundled data
- VERSION file embedded for version detection
- Single-file distribution per platform

### Configuration Precedence

```mermaid
flowchart TD
    ENV["1. Environment Variables<br/>(highest priority)"] --> DOTENV["2. .env File<br/>(does NOT override env vars)"]
    DOTENV --> INICFG["3. INI Config File"]
    INICFG --> DEFAULTS["4. Hardcoded Defaults<br/>(lowest priority)"]
```

---

## 11. Security Model

| Area | Implementation |
|------|----------------|
| **Authentication** | SHA-256 with 32-byte random salt; stored in INI as `sha256$salt$hash` |
| **SQL Injection** | All queries use parameterized `?` placeholders |
| **Data at Rest** | SQLite database (not encrypted); all data local |
| **Sensitive Data** | No cloud sync; no network calls; purely offline |
| **INI Security** | String interpolation disabled (`interpolation=None`) |
| **Atomic Writes** | JSON mappings use temp file + rename to prevent corruption |
| **Code Signing** | Not signed (macOS Gatekeeper bypass helper included) |

---

## 12. Supported Banks

Bank-specific formatters handle different CSV column layouts:

| Bank | Formatter | Notes |
|------|-----------|-------|
| Chase (credit + checking) | DefaultStatementFormatter | Standard format |
| Citi | CitiStatementFormatter | Inverts amount signs |
| Discover | DiscoverStatementFormatter | Inverts amount signs |
| Bilt | DefaultStatementFormatter | Standard format |

**Adding a new bank:**
1. Create a new formatter class extending `BaseStatementFormatter`
2. Override `_bank_specific_formatting()` for bank-specific logic
3. Register in the factory function (`statement_formatters/factory.py`)
4. Add column mapping section to INI config (`[newbank_map]`)
5. Add account entry under `[credit_cards]` or `[checking_accounts]`

---

## 13. Key Data Structures

### MonthlyReports (Frozen Dataclass)

Container for one month's financial data passed to dashboard pages:

| Field | Type | Description |
|-------|------|-------------|
| `month` | `pd.Period` | Month identifier (e.g., 2024-01) |
| `earnings` | `DataFrame` | Earnings transactions for the month |
| `expenses` | `DataFrame` | Expense transactions for the month |
| `expenses_category` | `DataFrame` | Category -> amount pivot table |
| `expenses_sub_category` | `DataFrame` | Sub-category -> amount pivot table |
| `transactions` | `DataFrame` | All transactions for the month |

### Canonical Transaction Schema

All bank CSVs are normalized to this schema before processing:

| Column | Type | Description |
|--------|------|-------------|
| `transaction_date` | datetime | Transaction date |
| `description` | str | Bank description |
| `amount` | float | Signed amount (+: earnings, -: expenses) |
| `from_account` | str | Account identifier |
| `sub_category` | str | Keyword-matched sub-category |
| `category` | str | Parent category |
| `c_or_d` | str | "earnings" or "expenditures" |

### Three-Level Category Hierarchy

```mermaid
flowchart LR
    D["Transaction Description<br/>(e.g., 'SAFEWAY #1234')"] -->|keyword substring match| SC["Sub-Category<br/>(e.g., 'Groceries')"]
    SC -->|exact match| C["Category<br/>(e.g., 'Needs')"]
    C -->|cashflow mapping| CF["Cashflow Type<br/>(e.g., 'Expenses')"]
```

---

## 14. Data Architecture

### Storage Overview

```mermaid
flowchart TD
    subgraph FileSystem["File System Storage"]
        CSV["statements/*.csv<br/>(Raw bank CSVs)"]
        JSON1["mappers/description_to_sub_category.json"]
        JSON2["mappers/sub_category_to_category.json"]
        JSON3["mappers/cashflow_to_category.json"]
        INI["config/budget_analyser.ini<br/>(Accounts, mappings, prefs)"]
        Logs["logs/gui_app.log<br/>(Rotating, 5MB x 3)"]
    end

    subgraph SQLite["SQLite Databases"]
        TxDB[("budget_analyser.db<br/>transactions table")]
        BudgetDB[("budget_goals.db<br/>4 tables: budget_goals,<br/>earnings_goals, accounts,<br/>recurring_transactions")]
    end

    subgraph Access["Database Access Layer"]
        BGRepo["features/budget_goals/<br/>repository.py<br/>(budget_goals, earnings_goals)"]
        LegacyBDB["infrastructure/<br/>budget_database.py<br/>(accounts, recurring_txns)"]
    end

    CSV -->|Ingestion| TxDB
    JSON1 -->|Categorization| TxDB
    JSON2 -->|Categorization| TxDB
    TxDB -->|Report Generation| Pages["Dashboard Pages"]
    BGRepo -->|"core.database<br/>get_connection()"| BudgetDB
    LegacyBDB -->|direct SQLite| BudgetDB
    BGRepo -->|Goal Tracking| Pages
    LegacyBDB -->|Accounts, Recurring| Pages
```

---

## 15. Future Extensibility

The architecture supports:

- **New features via vertical slices**: Create a new `features/<name>/` module with models, repository, service, controller, and page — self-contained and independently testable
- **Migrate existing features**: Follow the `budget_goals` pilot pattern — extract from horizontal layers into a vertical slice, leave backward-compat shims, remove shims once all consumers migrate
- **New bank formatters**: Add `StatementFormatter` subclass + factory registration
- **New report types**: Extend `ReportService` or create new domain services
- **New dashboard pages**: Add page to a feature slice or `views/pages/` and register in `dashboard_window.py`
- **New categorization rules**: Extend mapper JSON files via Mapper Hub UI
- **New analytics**: Add domain services (existing: forecasting, trends, burn rate, patterns)
- **Alternative storage backends**: Implement `StatementRepository` protocol for new sources
- **Export formats**: Extend `ExportService` with new format handlers
- **Multi-user support**: Would require authentication and data isolation refactor
- **Cloud sync**: Would require infrastructure layer additions
- **API layer**: Add REST endpoints consuming existing controllers for web/mobile clients

### Migration Roadmap

Remaining features to migrate to vertical slices (in order):

| Order | Feature | Source | Complexity |
|-------|---------|--------|------------|
| 1 | `net_worth` | BudgetController (accounts), NetWorthPage | Low |
| 2 | `recurring` | BudgetController (recurring), RecurringPage | Low |
| 3 | `savings` | BudgetController (savings), SavingsPage | Low |
| 4 | `ingestion` | transaction_ingestion.py, UploadController, UploadPage | Medium |
| 5 | `mappers` | MapperControllers, mapper pages | Medium |
| 6 | `reporting` | reporting.py, stats controllers, Earnings/ExpensesPage | Medium |
| 7 | `payments` | payment_matching.py, PaymentsController, PaymentsPage | Low |
| 8 | `forecasting` | forecasting.py | Low |
| 9 | `trends` | trend_analysis.py, spending_patterns.py | Low |
| 10 | `export` | export_service.py | Low |
| 11 | `settings` | SettingsController, SettingsPage | Low |

After `net_worth` + `recurring` + `savings` migrate, `BudgetController` and `BudgetDatabase` are fully decomposed and can be deleted.
