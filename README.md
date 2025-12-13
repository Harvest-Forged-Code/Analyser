# Budget Analyser

## Introduction

### Overview
Budget Analyser is an application designed to help users analyze and review their financial data by processing bank account statements. The application provides tools for categorizing transactions, generating reports, and visualizing financial data to help users better understand their spending habits and financial health.

### Purpose
The primary purpose of the Budget Analyser is to:
- Process and analyze bank account statements
- Categorize financial transactions automatically
- Generate detailed reports on earnings and expenses
- Provide insights into spending patterns and financial trends
- Help users make informed financial decisions

### Target Audience
- Individual users who want to track their personal finances
- Small business owners who need to monitor business expenses
- Financial advisors who assist clients with financial planning
- Anyone interested in gaining better insights into their financial data

## System Architecture
The Budget Analyser application follows a layered architecture pattern, specifically implementing the Model-View-Controller (MVC) design pattern with additional framework utilities. This architecture separates the application into distinct components, each with specific responsibilities, making the system more maintainable, extensible, and testable.

### Architectural Layers

#### View Layer
The View layer is responsible for the user interface components and user interaction. It includes:
- **Ui_Widget**: The login screen UI
- **Ui_MainWindow**: The main dashboard UI
- **InputDisplayApp** and **ExpenseReport**: Test UI components

#### Model Layer
The Model layer is responsible for data management and business logic. It includes:
- **Statements**: Collects and formats financial transaction data
- **OriginalStatement**: Provides raw transaction data
- **StatementFormatter**: Formats raw statements into a consistent format

#### Controller Layer
The Controller layer acts as an intermediary between the View and Model layers, processing user input and updating the model and view accordingly. It includes:
- **Report**: Generates various financial reports from transaction data
- **Processor**: Processes raw transactions by adding categorization

#### Framework Layer
The Framework layer provides utility classes and services used by the other layers. It includes:
- **Logger**: Provides centralized logging (implemented as a Singleton)
- **PandasToolkit**: Utility methods for pandas DataFrame operations
- **JsonHandler**: Handles JSON file loading and parsing

## Key Features
The Budget Analyser automatically categorizes transactions based on predefined rules and mappings, helping users understand where their money is going.

The application generates various financial reports, including:
- Earnings reports showing sources of income
- Expense reports showing where money is being spent
- Category-based reports showing spending by category
- Sub-category-based reports showing detailed spending patterns

The application groups data by month, allowing users to analyze their financial patterns over time and identify trends or anomalies.

The application features a modern, intuitive user interface with:
- A dark theme for reduced eye strain
- Clear navigation options
- Responsive design elements
- Tabular data presentation for easy comprehension

## Installation and Setup

### Prerequisites
Before installing the Budget Analyser, ensure you have the following prerequisites:

- Python 3.9 or higher
- pip (Python package installer)
- Required Python packages (listed in requirements.txt)

### Installation Steps
1. Clone the repository:
    ```
git clone https://github.com/username/Analyser.git
    cd Analyser
```
2. Install the required dependencies:
    ```
pip install -r requirements.txt
```
3. Set up any necessary configuration files (if applicable).

### Running the Application
To run the backend processing without the GUI (legacy CLI renderer under src/):

```
python source/main_be.py
```

To run the application with the graphical user interface (PySide6):

```
python -m budget_analyser
```

The GUI composition has been modularized for clarity and faster startup (reduced duplicate imports and object creation):
- src/budget_analyser/presentation/views/app_gui.py — composition and run_app()
- src/budget_analyser/presentation/views/login_window.py — LoginWindow (one class per file)
- src/budget_analyser/presentation/views/dashboard_window.py — DashboardWindow (one class per file)

Note: the legacy path `budget_analyser.presentation.views.gui_pyside6` has been removed. 
Please import `run_app` from `budget_analyser.presentation.views.app_gui` or simply run `python -m budget_analyser`.

## Usage Guide

### Logging In (GUI)
To log in to the Budget Analyser GUI:

1. Launch the application.
2. Enter the password in the password field (required: "123456").
3. Theme toggle: use the 🌙/☀️ button at the top-right of the login card to switch between Dark and Light themes. Your choice is remembered across restarts.
3. Click the "Login" button.

### Navigating the Dashboard
The dashboard provides a modern, theme‑aware experience with subtle shadows and rounded surfaces. Navigation options:

- Side panel navigation with sections (with emojis):
  - **🗓️ Yearly Summary**: Yearly overview with totals and monthly breakdown.
  - **💰 Earnings**: View reports on income sources.
  - **🧾 Expenses**: View reports on spending.
  - **⬆️ Upload**: Upload new statement data.
  - **🧭 Mapper**: Configure transaction categorization rules.
  - **⚙️ Settings**: Adjust application settings.
- Menu bar:
  - **File → Exit**: Quit the application (Cmd+Q on macOS, Ctrl+Q on Windows/Linux).
 - Header bar:
   - Theme toggle: use the 🌙/☀️ button at the top-right of the header to switch Dark/Light themes (persists across restarts).

Selecting a section in the side panel updates the central content area accordingly. The header bar shows the current section.

### Yearly Summary page
- Modern, clean layout with two equal-width panels summarizing Total Earned and Total Spent, including sub‑category tables.
- Monthly table lists all 12 months (missing data shown as 0), with improved typography and alternating row colors.

### Viewing Reports
To view financial reports:

1. Navigate to the desired report section (Earnings, Expenses, etc.).
2. Select the desired month from the month selector.
3. Review the tabular data presented in the report.

### Uploading Statements
To upload new statement data:

1. Navigate to the Upload section.
2. Follow the prompts to select and upload statement files.
3. The application will process the new data and update the reports.

---

*This README is automatically generated from the comprehensive documentation. For more details, please refer to the [full documentation](documentation/budget_analyser_documentation.pdf).*

*Last updated: 2025-08-10*
