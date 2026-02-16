# ---
# name: project-setup
# description: >
#   Use when initializing a new software project -- creates directory structure,
#   configuration files, CI/CD pipelines, virtual environment, and pyproject.toml.
#   Handles web APIs, data pipelines, ML projects, and Python libraries.
# trigger: >
#   When user asks to create, init, bootstrap, scaffold, or set up a new project.
#   Keywords: "new project", "init", "create project", "set up", "scaffold", "bootstrap".
# inputs:
#   - project_name: string (required)
#   - project_type: enum [web-api, data-pipeline, ml, library] (required)
#   - primary_framework: string (required, e.g., FastAPI, Flask, Luigi, PyTorch, etc.)
# references:
#   - CLAUDE.md [PYTHON] section for directory layout and conventions
#   - CLAUDE.md [ARCHITECTURE] section for structural patterns
# ---

# Skill: project-setup

## Purpose

Initialize a fully structured, production-ready Python project from scratch. The output
is a working repository with linting, testing, containerization, and CI/CD scaffolding
that conforms to the standards defined in CLAUDE.md.

---

## Workflow

### Step 1 -- Gather Requirements

Prompt the user for the following information. Do not proceed until all three are confirmed.

| Input              | Description                                      | Example            |
|--------------------|--------------------------------------------------|--------------------|
| `project_name`     | Snake_case name for the project                  | `order_service`    |
| `project_type`     | One of: web-api, data-pipeline, ml, library      | `web-api`          |
| `primary_framework`| The main framework or library to scaffold around | `FastAPI`          |

Validate:
- `project_name` must be a valid Python package name (lowercase, underscores, no hyphens).
- `project_type` must be one of the four enumerated values.
- `primary_framework` must be a real, installable Python package.

### Step 2 -- Create Directory Structure

Create the canonical directory layout per CLAUDE.md [PYTHON] section:

```
{project_name}/
  src/
    {project_name}/
      __init__.py
      main.py
      config.py
      core/
        __init__.py
      models/
        __init__.py
      services/
        __init__.py
      utils/
        __init__.py
  tests/
    __init__.py
    conftest.py
    unit/
      __init__.py
    integration/
      __init__.py
  scripts/
  docs/
  .github/
    workflows/
  docker/
```

Conditional additions based on `project_type`:
- **web-api**: add `src/{project_name}/api/`, `src/{project_name}/api/routers/`, `src/{project_name}/api/schemas/`, `src/{project_name}/api/dependencies/`
- **data-pipeline**: add `src/{project_name}/pipelines/`, `src/{project_name}/extractors/`, `src/{project_name}/transformers/`, `src/{project_name}/loaders/`, `data/raw/`, `data/processed/`
- **ml**: add `src/{project_name}/models/`, `src/{project_name}/training/`, `src/{project_name}/inference/`, `src/{project_name}/features/`, `data/raw/`, `data/processed/`, `notebooks/`
- **library**: add `src/{project_name}/core/`, `src/{project_name}/exceptions.py`, `examples/`

### Step 3 -- Create pyproject.toml

Generate `pyproject.toml` with:

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "{project_name}"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    # Populated based on project_type -- see dependency map below
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "pytest-asyncio>=0.21",
    "ruff>=0.5.0",
    "mypy>=1.5",
    "pre-commit>=3.4",
]
```

**Dependency map by project_type:**
- **web-api**: `fastapi`, `uvicorn[standard]`, `pydantic>=2.0`, `pydantic-settings`, `httpx`, `sqlalchemy[asyncio]>=2.0`, `alembic`
- **data-pipeline**: `pandas>=2.0`, `sqlalchemy>=2.0`, `click`, `pydantic>=2.0`, `schedule` or framework-specific deps
- **ml**: `torch` or `tensorflow`, `numpy`, `pandas>=2.0`, `scikit-learn`, `mlflow`, `pydantic>=2.0`
- **library**: `pydantic>=2.0` (minimal, user-driven)

Adjust if user specified a different `primary_framework`.

### Step 4 -- Create .gitignore, .env.example, Makefile

**.gitignore** -- Use the comprehensive Python gitignore template:
- `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `.env`, `*.egg-info/`, `dist/`, `build/`
- `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`
- IDE files: `.idea/`, `.vscode/`, `*.swp`
- Data files if applicable: `data/raw/`, `*.csv`, `*.parquet` (for ml/data-pipeline)

**.env.example** -- Scaffold with placeholder variables:
```env
# Application
APP_ENV=development
APP_DEBUG=true
APP_LOG_LEVEL=INFO

# Database (if web-api or data-pipeline)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/{project_name}

# Secrets
SECRET_KEY=changeme
```

**Makefile** -- Include standard targets:
```makefile
.PHONY: install lint test run clean docker-build docker-up

install:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/
	mypy src/

test:
	pytest tests/ -v --cov=src/{project_name} --cov-report=term-missing

run:
	# Varies by project_type

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov dist build *.egg-info

docker-build:
	docker compose build

docker-up:
	docker compose up -d
```

### Step 5 -- Create Dockerfile and docker-compose.yml

**Dockerfile** (multi-stage):
```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

FROM base AS production
COPY src/ src/
# CMD varies by project_type
```

**docker-compose.yml**:
- Service for the application.
- For web-api: add postgres service, redis service (optional).
- For data-pipeline: add postgres or relevant data stores.
- For ml: add volume mounts for data and model artifacts.
- For library: minimal compose, primarily for testing.

Include `.env` file reference, health checks, and volume mounts.

### Step 6 -- Create Source Scaffolds

**src/{project_name}/__init__.py**:
```python
"""Top-level package for {project_name}."""

__version__ = "0.1.0"
```

**src/{project_name}/main.py** -- Varies by project_type:
- **web-api**: FastAPI app factory with lifespan, CORS, exception handlers.
- **data-pipeline**: CLI entry point with click or argparse.
- **ml**: Training/inference entry point.
- **library**: Minimal; public API re-exports.

**src/{project_name}/config.py**:
```python
"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    app_debug: bool = False
    app_log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
```

### Step 7 -- Create Test Scaffolds

**tests/conftest.py** with base fixtures:
```python
"""Shared test fixtures."""

import pytest

@pytest.fixture
def app_settings():
    """Override settings for test environment."""
    from {project_name}.config import Settings
    return Settings(app_env="testing", app_debug=True)
```

Additional fixtures by project_type:
- **web-api**: `async_client` fixture using `httpx.AsyncClient`, test database session fixture.
- **data-pipeline**: temp directory fixture, sample data fixtures.
- **ml**: sample tensor/dataframe fixtures, mock model fixture.

### Step 8 -- Initialize Git Repository

```bash
git init
git add -A
git commit -m "feat: initial project scaffold for {project_name}

Project type: {project_type}
Framework: {primary_framework}

Generated directory structure, pyproject.toml, Docker config,
test scaffolds, and development tooling."
```

### Step 9 -- Configure Ruff in pyproject.toml

Append to `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py311"
line-length = 100
src = ["src"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "S",    # flake8-bandit
    "A",    # flake8-builtins
    "C4",   # flake8-comprehensions
    "RET",  # flake8-return
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
    "PTH",  # flake8-use-pathlib
    "RUF",  # Ruff-specific rules
]
ignore = ["S101"]  # Allow assert in tests

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "S106"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-ra -q"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

### Step 10 -- Verify

Run all verification checks and report results:

```bash
# 1. Lint check
ruff check src/ tests/

# 2. Format check
ruff format --check src/ tests/

# 3. Test run
pytest tests/ -v

# 4. Structure verification
find . -type f -name "*.py" | head -20
```

All three must pass (or show expected "no tests collected" for empty test files).
Report any issues and fix them before finishing.

---

## Enforced Standards

### Google-Style Docstrings (MANDATORY)
Every function, method, and class written or modified during project setup MUST have a Google-style docstring. No exceptions. This includes:
- One-line summary in imperative mood
- Args section for all parameters
- Returns section describing what is returned
- Raises section for all exceptions
- See CLAUDE.md [STANDARDS] for full specification and examples.

### Git Commit Format (MANDATORY)
All commits created during project setup MUST follow this format:
- **Signed commits**: Always use `git commit -S`
- **Semantic prefix**: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`, `ci:`
- **File-change table** in the commit body:
  ```
  type: concise description

  | File (Location) | Summary of Change |
  |---|---|
  | path/to/file.py | What changed in this file |

  Author: PrabhukumarSivamoorthy@gmail.com
  ```
- See CLAUDE.md [GIT] for full specification.

---

## Completion Checklist

Before declaring the project setup complete, verify every item:

- [ ] Project name is valid Python package name
- [ ] Directory structure matches CLAUDE.md [PYTHON] section
- [ ] `pyproject.toml` has correct dependencies for project type
- [ ] `.gitignore` covers all standard patterns
- [ ] `.env.example` has all required environment variables
- [ ] `Makefile` has install, lint, test, run, clean, docker targets
- [ ] `Dockerfile` uses multi-stage build
- [ ] `docker-compose.yml` includes all required services
- [ ] `__init__.py` exists in all packages
- [ ] `main.py` has appropriate entry point for project type
- [ ] `config.py` uses pydantic-settings
- [ ] `conftest.py` has base fixtures for project type
- [ ] Git repo initialized with clean initial commit
- [ ] Ruff config in `pyproject.toml` with comprehensive rule set
- [ ] `ruff check` passes clean
- [ ] `pytest` runs without errors
- [ ] No hardcoded secrets in any file
- [ ] README.md stub exists (even if minimal)
