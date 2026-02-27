# Sidecar Bundling Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Bundle the Python FastAPI backend into a PyInstaller one-file binary that Tauri launches as a managed sidecar, producing a true standalone `.dmg` and `.exe` with no Python dependency on the user's machine.

**Architecture:** PyInstaller freezes `src/budget_analyser/api/main.py` and all dependencies into a single native binary per platform. Tauri resolves the binary from the same directory as the main executable and spawns it with `BUDGET_ANALYSER_DATA_DIR` set to the OS app data directory. The Python backend seeds default data on first launch, then reads/writes user data exclusively from that directory.

**Tech Stack:** PyInstaller ≥6.0, Tauri v2, `tauri-plugin-shell`, `app.path().app_data_dir()`, GitHub Actions matrix (macos-latest ARM, macos-13 Intel, windows-latest).

---

## Task 1: Add PyInstaller and create the spec file

**Files:**
- Modify: `pyproject.toml`
- Create: `budget-analyser-api.spec` (project root)

**Step 1: Add pyinstaller to dev dependencies**

In `pyproject.toml`, add to `[dependency-groups] dev`:
```toml
[dependency-groups]
dev = [
    "pytest~=8.3.4",
    "pylint>=3.0",
    "httpx>=0.27.0",
    "pyinstaller>=6.0",
]
```

Run: `uv sync --group dev`

**Step 2: Create the spec file**

Create `budget-analyser-api.spec` at the project root:

```python
# budget-analyser-api.spec
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# Allow importlib.metadata.version("budget-analyser") to work when frozen
datas = copy_metadata("budget-analyser")

# Bundle seed data (mappers + config) as read-only assets
datas += [
    ("src/budget_analyser/data/mappers", "data/mappers"),
    ("src/budget_analyser/data/config", "data/config"),
]

# uvicorn dynamic imports that PyInstaller misses
datas += collect_data_files("uvicorn")

a = Analysis(
    ["src/budget_analyser/api/main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# One-file mode: single executable, no extraction directory needed
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="budget-analyser-api",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    target_arch=None,
)
```

**Step 3: Run PyInstaller and verify binary exists**

```bash
uv run pyinstaller budget-analyser-api.spec --clean
```

Expected output: `dist/budget-analyser-api` (macOS/Linux) or `dist/budget-analyser-api.exe` (Windows).

**Step 4: Smoke-test the binary**

```bash
# macOS/Linux
BUDGET_ANALYSER_DATA_DIR=/tmp/ba-test ./dist/budget-analyser-api &
sleep 3
curl http://127.0.0.1:8741/api/health
# Expected: {"status":"healthy"}
kill %1
```

**Step 5: Add dist/ and build/ to .gitignore**

```bash
echo "\n# PyInstaller\ndist/\nbuild/\n*.spec.bak" >> .gitignore
```

**Step 6: Commit**

```bash
git add pyproject.toml budget-analyser-api.spec .gitignore
git commit -S -m "feat(sidecar): add PyInstaller spec for frozen Python API binary

| Area                      | Change                                      |
|---------------------------|---------------------------------------------|
| pyproject.toml            | Added pyinstaller>=6.0 to dev dependencies  |
| budget-analyser-api.spec  | One-file PyInstaller spec with seed datas   |
| .gitignore                | Ignore dist/ build/ PyInstaller artifacts   |

Author: Prabhukumar Sivamorthy"
```

---

## Task 2: Add BUDGET_ANALYSER_DATA_DIR support to settings.py

`settings.py` already supports per-path env vars. We add a single `BUDGET_ANALYSER_DATA_DIR` override that sets all paths relative to one root directory.

**Files:**
- Modify: `src/budget_analyser/settings/settings.py`
- Create: `src/test/unit/test_settings.py`

**Step 1: Write the failing test first**

Create `src/test/unit/test_settings.py`:

```python
"""Tests for settings data-dir resolution."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from budget_analyser.settings.settings import load_settings


def test_data_dir_env_var_sets_all_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """BUDGET_ANALYSER_DATA_DIR overrides all individual path settings."""
    monkeypatch.setenv("BUDGET_ANALYSER_DATA_DIR", str(tmp_path))
    # Clear individual overrides so data_dir takes precedence
    for key in [
        "BUDGET_ANALYSER_STATEMENT_DIR",
        "BUDGET_ANALYSER_INI_CONFIG_PATH",
        "BUDGET_ANALYSER_DESCRIPTION_TO_SUB_CATEGORY_PATH",
        "BUDGET_ANALYSER_SUB_CATEGORY_TO_CATEGORY_PATH",
        "BUDGET_ANALYSER_CASHFLOW_TO_CATEGORY_PATH",
        "BUDGET_ANALYSER_DATABASE_PATH",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = load_settings()

    assert settings.statement_dir == tmp_path / "statements"
    assert settings.ini_config_path == tmp_path / "config" / "budget_analyser.ini"
    assert settings.description_to_sub_category_path == tmp_path / "mappers" / "description_to_sub_category.json"
    assert settings.sub_category_to_category_path == tmp_path / "mappers" / "sub_category_to_category.json"
    assert settings.cashflow_to_category_path == tmp_path / "mappers" / "cashflow_to_category.json"
    assert settings.database_path == tmp_path / "budget_analyser.db"


def test_data_dir_absent_uses_existing_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without BUDGET_ANALYSER_DATA_DIR, existing per-path env vars still work."""
    monkeypatch.delenv("BUDGET_ANALYSER_DATA_DIR", raising=False)
    monkeypatch.setenv("BUDGET_ANALYSER_DATABASE_PATH", "/tmp/test.db")

    settings = load_settings()

    assert settings.database_path == Path("/tmp/test.db")
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest src/test/unit/test_settings.py -v
```

Expected: FAIL — `BUDGET_ANALYSER_DATA_DIR` not yet handled in `load_settings`.

**Step 3: Update load_settings() in settings.py**

In `src/budget_analyser/settings/settings.py`, replace `load_settings()` with:

```python
def load_settings() -> Settings:
    """Load application settings from environment (and optional `.env`).

    When ``BUDGET_ANALYSER_DATA_DIR`` is set, all paths are derived from it.
    Individual path env vars are still honoured when the data-dir var is absent.

    Environment variables:
    - BUDGET_ANALYSER_DATA_DIR (takes precedence — sets all paths under one root)
    - BUDGET_ANALYSER_STATEMENT_DIR
    - BUDGET_ANALYSER_INI_CONFIG_PATH
    - BUDGET_ANALYSER_DESCRIPTION_TO_SUB_CATEGORY_PATH
    - BUDGET_ANALYSER_SUB_CATEGORY_TO_CATEGORY_PATH
    - BUDGET_ANALYSER_CASHFLOW_TO_CATEGORY_PATH
    - BUDGET_ANALYSER_DATABASE_PATH
    - BUDGET_ANALYSER_LOG_LEVEL
    """
    root = _project_root()
    pkg_root = _package_root()
    _load_dotenv(root / ".env")

    data_dir_str = os.environ.get("BUDGET_ANALYSER_DATA_DIR", "")
    if data_dir_str:
        data_dir = Path(data_dir_str)
        return Settings(
            statement_dir=data_dir / "statements",
            ini_config_path=data_dir / "config" / "budget_analyser.ini",
            description_to_sub_category_path=data_dir / "mappers" / "description_to_sub_category.json",
            sub_category_to_category_path=data_dir / "mappers" / "sub_category_to_category.json",
            cashflow_to_category_path=data_dir / "mappers" / "cashflow_to_category.json",
            database_path=data_dir / "budget_analyser.db",
            log_level=os.environ.get("BUDGET_ANALYSER_LOG_LEVEL", "INFO"),
        )

    statement_dir = Path(
        os.environ.get(
            "BUDGET_ANALYSER_STATEMENT_DIR",
            str(pkg_root / "data" / "statements"),
        )
    )
    ini_config_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_INI_CONFIG_PATH",
            str(pkg_root / "data" / "config" / "budget_analyser.ini"),
        )
    )
    description_to_sub_category_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_DESCRIPTION_TO_SUB_CATEGORY_PATH",
            str(pkg_root / "data" / "mappers" / "description_to_sub_category.json"),
        )
    )
    sub_category_to_category_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_SUB_CATEGORY_TO_CATEGORY_PATH",
            str(pkg_root / "data" / "mappers" / "sub_category_to_category.json"),
        )
    )
    cashflow_to_category_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_CASHFLOW_TO_CATEGORY_PATH",
            str(pkg_root / "data" / "mappers" / "cashflow_to_category.json"),
        )
    )
    database_path = Path(
        os.environ.get(
            "BUDGET_ANALYSER_DATABASE_PATH",
            str(pkg_root / "data" / "budget_analyser.db"),
        )
    )
    log_level = os.environ.get("BUDGET_ANALYSER_LOG_LEVEL", "INFO")

    return Settings(
        statement_dir=statement_dir,
        ini_config_path=ini_config_path,
        description_to_sub_category_path=description_to_sub_category_path,
        sub_category_to_category_path=sub_category_to_category_path,
        cashflow_to_category_path=cashflow_to_category_path,
        database_path=database_path,
        log_level=log_level,
    )
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest src/test/unit/test_settings.py -v
```

Expected: PASS (both tests green).

**Step 5: Run all unit tests to check for regressions**

```bash
uv run pytest src/test/unit/ -q
```

Expected: all existing tests still pass.

**Step 6: Commit**

```bash
git add src/budget_analyser/settings/settings.py src/test/unit/test_settings.py
git commit -S -m "feat(settings): add BUDGET_ANALYSER_DATA_DIR single-root path override

| Area                    | Change                                          |
|-------------------------|-------------------------------------------------|
| settings/settings.py    | BUDGET_ANALYSER_DATA_DIR sets all paths from    |
|                         | one root; per-path vars still work as fallback  |
| test_settings.py        | Unit tests for data-dir resolution              |

Author: Prabhukumar Sivamorthy"
```

---

## Task 3: Add first-launch data seeding to the Python backend

When the frozen binary starts with `BUDGET_ANALYSER_DATA_DIR` pointing to a new directory, it must seed default mappers and config before FastAPI initialises.

**Files:**
- Create: `src/budget_analyser/settings/seeding.py`
- Modify: `src/budget_analyser/api/main.py`
- Create: `src/test/unit/test_seeding.py`

**Step 1: Write the failing tests**

Create `src/test/unit/test_seeding.py`:

```python
"""Tests for first-launch data seeding."""
from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from budget_analyser.settings.seeding import seed_data_directory


@pytest.fixture()
def bundle_data(tmp_path: Path) -> Path:
    """Create a fake PyInstaller bundle data directory."""
    bundle = tmp_path / "bundle_data"
    (bundle / "mappers").mkdir(parents=True)
    (bundle / "config").mkdir(parents=True)
    (bundle / "mappers" / "description_to_sub_category.json").write_text("{}")
    (bundle / "mappers" / "sub_category_to_category.json").write_text("{}")
    (bundle / "mappers" / "cashflow_to_category.json").write_text("{}")
    (bundle / "config" / "budget_analyser.ini").write_text("[DEFAULT]")
    return bundle


def test_seeds_empty_data_dir(tmp_path: Path, bundle_data: Path) -> None:
    """Empty data dir gets mappers, config, statements, and logs."""
    data_dir = tmp_path / "user_data"
    data_dir.mkdir()

    with patch("budget_analyser.settings.seeding._bundle_data_dir", return_value=bundle_data):
        seed_data_directory(data_dir)

    assert (data_dir / "mappers" / "description_to_sub_category.json").exists()
    assert (data_dir / "config" / "budget_analyser.ini").exists()
    assert (data_dir / "statements").is_dir()
    assert (data_dir / "logs").is_dir()


def test_skips_if_mappers_already_exist(tmp_path: Path, bundle_data: Path) -> None:
    """Existing mappers are not overwritten."""
    data_dir = tmp_path / "user_data"
    (data_dir / "mappers").mkdir(parents=True)
    existing = data_dir / "mappers" / "description_to_sub_category.json"
    existing.write_text('{"custom": true}')

    with patch("budget_analyser.settings.seeding._bundle_data_dir", return_value=bundle_data):
        seed_data_directory(data_dir)

    assert existing.read_text() == '{"custom": true}'


def test_no_op_when_bundle_data_absent(tmp_path: Path) -> None:
    """When not running frozen (dev mode), seeding does nothing."""
    data_dir = tmp_path / "user_data"
    data_dir.mkdir()

    with patch("budget_analyser.settings.seeding._bundle_data_dir", return_value=None):
        seed_data_directory(data_dir)

    assert not (data_dir / "mappers").exists()
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest src/test/unit/test_seeding.py -v
```

Expected: FAIL — module does not exist yet.

**Step 3: Create seeding.py**

Create `src/budget_analyser/settings/seeding.py`:

```python
"""First-launch data seeding for the standalone desktop app.

When Budget Analyser runs as a PyInstaller-frozen binary, user data lives
in the OS app data directory.  This module copies bundled seed files there
on the very first launch, then stays out of the way on subsequent launches.
"""

from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

_log = logging.getLogger(__name__)


def _bundle_data_dir() -> Path | None:
    """Return the bundled seed data directory, or None in dev mode.

    Returns:
        Path to ``data/`` inside the PyInstaller ``_MEIPASS`` directory,
        or ``None`` when running from source (not frozen).
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "data"  # type: ignore[attr-defined]
    return None


def seed_data_directory(data_dir: Path) -> None:
    """Copy bundled seed files to *data_dir* on first launch.

    Only runs when the app is frozen (PyInstaller).  Existing user files
    are never overwritten.

    Args:
        data_dir: The OS app data directory (``BUDGET_ANALYSER_DATA_DIR``).
    """
    bundle = _bundle_data_dir()
    if bundle is None:
        _log.debug("Dev mode — skipping data seeding")
        return

    data_dir.mkdir(parents=True, exist_ok=True)

    for subdir in ("mappers", "config"):
        src = bundle / subdir
        dst = data_dir / subdir
        if not dst.exists() and src.exists():
            shutil.copytree(src, dst)
            _log.info("Seeded %s from bundle", dst)

    for subdir in ("statements", "logs"):
        (data_dir / subdir).mkdir(exist_ok=True)
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest src/test/unit/test_seeding.py -v
```

Expected: all 3 tests PASS.

**Step 5: Call seeding from api/main.py before uvicorn starts**

In `src/budget_analyser/api/main.py`, add the import at the top with other imports:

```python
import os
from pathlib import Path
from budget_analyser.settings.seeding import seed_data_directory
```

Then add the `_bootstrap_data_dir()` call inside the `if __name__ == "__main__":` block AND as the first thing in `_lifespan`:

Replace the existing `_lifespan` with:

```python
@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Seed data directory then initialise shared controllers on startup."""
    data_dir_env = os.environ.get("BUDGET_ANALYSER_DATA_DIR", "")
    if data_dir_env:
        seed_data_directory(Path(data_dir_env))
    dependencies.initialize()
    yield
```

**Step 6: Run all unit tests**

```bash
uv run pytest src/test/unit/ -q
```

Expected: all tests pass.

**Step 7: Commit**

```bash
git add src/budget_analyser/settings/seeding.py src/budget_analyser/api/main.py src/test/unit/test_seeding.py
git commit -S -m "feat(sidecar): add first-launch data seeding for standalone app

| Area                    | Change                                          |
|-------------------------|-------------------------------------------------|
| settings/seeding.py     | New module: copies bundled seed data to         |
|                         | BUDGET_ANALYSER_DATA_DIR on first launch        |
| api/main.py             | Call seed_data_directory() in lifespan startup  |
| test_seeding.py         | Unit tests: seeding, skip-if-exists, dev no-op  |

Author: Prabhukumar Sivamorthy"
```

---

## Task 4: Update Tauri to launch the sidecar

Replace the current ad-hoc Python search in `lib.rs` with platform-aware sidecar launch. In release builds, find the binary next to the app executable. In debug builds, keep the existing `.venv/bin/python` fallback.

**Files:**
- Modify: `src/frontend/src-tauri/src/lib.rs`
- Modify: `src/frontend/src-tauri/tauri.conf.json`
- Create: `src/frontend/src-tauri/binaries/.gitkeep`

**Step 1: Create the binaries directory with a gitkeep**

```bash
mkdir -p src/frontend/src-tauri/binaries
touch src/frontend/src-tauri/binaries/.gitkeep
echo "src/frontend/src-tauri/binaries/*" >> .gitignore
echo "!src/frontend/src-tauri/binaries/.gitkeep" >> .gitignore
```

**Step 2: Add externalBin to tauri.conf.json**

In `src/frontend/src-tauri/tauri.conf.json`, add a `bundle` section after `plugins`:

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "Budget Analyser",
  "version": "1.0.0",
  "identifier": "com.budgetanalyser.app",
  "build": {
    "frontendDist": "../dist",
    "devUrl": "http://localhost:5173",
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build"
  },
  "bundle": {
    "externalBin": ["binaries/budget-analyser-api"]
  },
  "app": {
    "windows": [
      {
        "title": "Budget Analyser",
        "width": 1280,
        "height": 800,
        "minWidth": 1024,
        "minHeight": 768,
        "center": true
      }
    ],
    "security": {
      "csp": null
    }
  },
  "plugins": {
    "shell": {
      "open": true
    }
  }
}
```

**Step 3: Rewrite lib.rs**

Replace the entire content of `src/frontend/src-tauri/src/lib.rs` with:

```rust
use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;

struct ApiProcess(Mutex<Option<Child>>);

// ── Sidecar path resolution (release builds only) ────────────────────────────

#[cfg(not(debug_assertions))]
fn resolve_sidecar_path() -> Option<PathBuf> {
    let exe_dir = std::env::current_exe().ok()?.parent()?.to_path_buf();
    let name = if cfg!(windows) {
        "budget-analyser-api.exe"
    } else {
        "budget-analyser-api"
    };
    let path = exe_dir.join(name);
    path.exists().then_some(path)
}

// ── API launch (release) ──────────────────────────────────────────────────────

#[cfg(not(debug_assertions))]
fn start_python_api(data_dir: &PathBuf) -> Option<Child> {
    if check_api_health() {
        println!("Python API already running on port 8741");
        return None;
    }

    let sidecar = match resolve_sidecar_path() {
        Some(p) => p,
        None => {
            eprintln!("Sidecar binary not found next to app executable");
            return None;
        }
    };

    println!("Starting sidecar: {:?}", sidecar);
    match Command::new(&sidecar)
        .env("BUDGET_ANALYSER_DATA_DIR", data_dir.to_string_lossy().as_ref())
        .spawn()
    {
        Ok(child) => {
            println!("Sidecar started (pid: {})", child.id());
            Some(child)
        }
        Err(e) => {
            eprintln!("Failed to start sidecar: {}", e);
            None
        }
    }
}

// ── API launch (dev / debug) ──────────────────────────────────────────────────

#[cfg(debug_assertions)]
fn find_project_root() -> PathBuf {
    let cwd = std::env::current_dir().unwrap_or_default();
    if cwd.ends_with("frontend") {
        cwd.parent()
            .and_then(|p| p.parent())
            .map(|p| p.to_path_buf())
            .unwrap_or(cwd)
    } else if cwd.ends_with("src") {
        cwd.parent().map(|p| p.to_path_buf()).unwrap_or(cwd)
    } else {
        cwd
    }
}

#[cfg(debug_assertions)]
fn start_python_api(_data_dir: &PathBuf) -> Option<Child> {
    if check_api_health() {
        println!("Python API already running on port 8741");
        return None;
    }

    let project_root = find_project_root();
    let candidates: Vec<PathBuf> = vec![
        project_root.join(".venv/bin/python"),
        PathBuf::from("python3"),
        PathBuf::from("python"),
    ];

    for python in &candidates {
        match Command::new(python)
            .args(["-m", "budget_analyser.api.main"])
            .current_dir(&project_root)
            .spawn()
        {
            Ok(child) => {
                println!("Dev: started Python API (pid: {})", child.id());
                std::thread::sleep(Duration::from_secs(2));
                return Some(child);
            }
            Err(_) => continue,
        }
    }

    eprintln!("Dev: could not start Python API");
    None
}

// ── Health check ─────────────────────────────────────────────────────────────

fn check_api_health() -> bool {
    reqwest::blocking::get("http://127.0.0.1:8741/api/health")
        .map(|r| r.status().is_success())
        .unwrap_or(false)
}

// ── Tauri entry point ─────────────────────────────────────────────────────────

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let data_dir = app
                .path()
                .app_data_dir()
                .expect("Failed to resolve app data directory");

            println!("App data directory: {:?}", data_dir);

            let child = start_python_api(&data_dir);
            app.manage(ApiProcess(Mutex::new(child)));

            // Poll health check — 20 attempts × 500 ms = 10 s max
            let mut healthy = false;
            for attempt in 1..=20 {
                if check_api_health() {
                    println!("API health check passed (attempt {})", attempt);
                    healthy = true;
                    break;
                }
                std::thread::sleep(Duration::from_millis(500));
            }

            if !healthy {
                eprintln!("Warning: Python API did not respond after 10 s");
            }

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                let app = window.app_handle();
                if let Some(state) = app.try_state::<ApiProcess>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(ref mut child) = *guard {
                            println!("Shutting down API sidecar (pid: {})", child.id());
                            let _ = child.kill();
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

**Step 4: Verify dev mode still works**

```bash
cd src/frontend && npm run tauri dev
```

Expected: App opens, Python API starts via `.venv/bin/python`, no Rust compile errors.

**Step 5: Commit**

```bash
git add src/frontend/src-tauri/src/lib.rs \
        src/frontend/src-tauri/tauri.conf.json \
        src/frontend/src-tauri/binaries/.gitkeep \
        .gitignore
git commit -S -m "feat(sidecar): update Tauri to launch PyInstaller sidecar in release builds

| Area                   | Change                                            |
|------------------------|---------------------------------------------------|
| lib.rs                 | cfg(debug_assertions) split: sidecar in release,  |
|                        | .venv/python fallback in debug; passes             |
|                        | BUDGET_ANALYSER_DATA_DIR via app_data_dir()        |
| tauri.conf.json        | Added bundle.externalBin for sidecar binary        |
| binaries/.gitkeep      | Placeholder for CI-built sidecar binaries          |
| .gitignore             | Ignore sidecar binaries except .gitkeep            |

Author: Prabhukumar Sivamorthy"
```

---

## Task 5: Update build-check.yml with PyInstaller build jobs

Add three Python build jobs (macOS ARM, macOS Intel, Windows) that produce the sidecar binary and pass it to the Tauri build jobs.

**Files:**
- Modify: `.github/workflows/build-check.yml`

**Step 1: Replace build-check.yml with the full updated version**

```yaml
name: Build Check

on:
  workflow_dispatch:
    inputs:
      version:
        description: "Version string to use (e.g. 1.0.99)"
        required: false
        default: "0.0.0-build-check"

permissions:
  contents: read

jobs:
  # ── Step 1: Build PyInstaller sidecar binary per platform ─────────────────
  build-python:
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: macos-latest
            triple: aarch64-apple-darwin
          - os: macos-13
            triple: x86_64-apple-darwin
          - os: windows-latest
            triple: x86_64-pc-windows-msvc

    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          python-version: "3.12"

      - name: Install Python dependencies (including pyinstaller)
        run: uv sync --group dev

      - name: Build sidecar binary
        run: uv run pyinstaller budget-analyser-api.spec --clean --distpath dist-sidecar

      - name: Smoke-test sidecar binary (Unix)
        if: runner.os != 'Windows'
        run: |
          mkdir -p /tmp/ba-test
          BUDGET_ANALYSER_DATA_DIR=/tmp/ba-test ./dist-sidecar/budget-analyser-api &
          SIDECAR_PID=$!
          sleep 5
          curl --fail http://127.0.0.1:8741/api/health
          kill $SIDECAR_PID
        shell: bash

      - name: Smoke-test sidecar binary (Windows)
        if: runner.os == 'Windows'
        run: |
          $env:BUDGET_ANALYSER_DATA_DIR = "$env:TEMP\ba-test"
          New-Item -ItemType Directory -Force -Path $env:BUDGET_ANALYSER_DATA_DIR
          $proc = Start-Process -FilePath "dist-sidecar\budget-analyser-api.exe" -PassThru
          Start-Sleep -Seconds 5
          Invoke-RestMethod http://127.0.0.1:8741/api/health
          Stop-Process -Id $proc.Id
        shell: pwsh

      - name: Stage binary with target triple name (Unix)
        if: runner.os != 'Windows'
        run: |
          mkdir -p src/frontend/src-tauri/binaries
          cp dist-sidecar/budget-analyser-api \
             src/frontend/src-tauri/binaries/budget-analyser-api-${{ matrix.triple }}
          chmod +x src/frontend/src-tauri/binaries/budget-analyser-api-${{ matrix.triple }}
        shell: bash

      - name: Stage binary with target triple name (Windows)
        if: runner.os == 'Windows'
        run: |
          New-Item -ItemType Directory -Force -Path src/frontend/src-tauri/binaries
          Copy-Item "dist-sidecar\budget-analyser-api.exe" `
            "src\frontend\src-tauri\binaries\budget-analyser-api-${{ matrix.triple }}.exe"
        shell: pwsh

      - name: Upload sidecar artifact
        uses: actions/upload-artifact@v4
        with:
          name: sidecar-${{ matrix.triple }}
          path: src/frontend/src-tauri/binaries/
          if-no-files-found: error

  # ── Step 2: Build Tauri installer per platform ────────────────────────────
  build-tauri:
    needs: build-python
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: windows-latest
            label: Windows
            triple: x86_64-pc-windows-msvc
            artifact_glob: "src/frontend/src-tauri/target/release/bundle/nsis/*.exe"
          - os: macos-latest
            label: macOS_AppleSilicon
            triple: aarch64-apple-darwin
            artifact_glob: "src/frontend/src-tauri/target/release/bundle/dmg/*.dmg"
          - os: macos-13
            label: macOS_Intel
            triple: x86_64-apple-darwin
            artifact_glob: "src/frontend/src-tauri/target/release/bundle/dmg/*.dmg"

    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          python-version: "3.12"

      - name: Install Python dependencies
        run: uv sync

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22

      - name: Install frontend dependencies
        working-directory: src/frontend
        run: npm ci

      - name: Install Rust stable
        uses: dtolnay/rust-toolchain@stable

      - name: Rust cache
        uses: swatinem/rust-cache@v2
        with:
          workspaces: src/frontend/src-tauri

      - name: Download sidecar binary
        uses: actions/download-artifact@v4
        with:
          name: sidecar-${{ matrix.triple }}
          path: src/frontend/src-tauri/binaries/

      - name: Make sidecar executable (Unix)
        if: runner.os != 'Windows'
        run: chmod +x src/frontend/src-tauri/binaries/budget-analyser-api-${{ matrix.triple }}

      - name: Set version in tauri.conf.json
        shell: bash
        run: |
          VERSION="${{ github.event.inputs.version }}"
          cd src/frontend/src-tauri
          python3 -c "
          import json
          with open('tauri.conf.json', 'r') as f:
              conf = json.load(f)
          conf['version'] = '$VERSION'
          with open('tauri.conf.json', 'w') as f:
              json.dump(conf, f, indent=2)
          "

      - name: Build Tauri app
        working-directory: src/frontend
        run: npm run tauri build

      - name: Upload installer artifact
        uses: actions/upload-artifact@v4
        with:
          name: budget-analyser-${{ matrix.label }}
          path: ${{ matrix.artifact_glob }}
          if-no-files-found: error
          retention-days: 7
```

**Step 2: Commit**

```bash
git add .github/workflows/build-check.yml
git commit -S -m "feat(ci): add PyInstaller build jobs to build-check workflow

| Area                           | Change                                      |
|--------------------------------|---------------------------------------------|
| .github/workflows/build-check  | Added build-python matrix job (ARM, Intel,  |
|                                | Windows); smoke-tests each binary; passes   |
|                                | artifact to build-tauri job per platform    |

Author: Prabhukumar Sivamorthy"
```

---

## Task 6: Update release.yml with the same PyInstaller build jobs

**Files:**
- Modify: `.github/workflows/release.yml`

**Step 1: Add build-python job and update build-tauri in release.yml**

After the existing `version-and-tag` job, add the `build-python` job (identical to build-check.yml but gated on `should_release == 'true'`), then update `build-tauri` to depend on it and download the artifact.

Replace the `build-tauri` job and add `build-python` before it:

```yaml
  build-python:
    needs: version-and-tag
    if: needs.version-and-tag.outputs.should_release == 'true'
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: macos-latest
            triple: aarch64-apple-darwin
          - os: macos-13
            triple: x86_64-apple-darwin
          - os: windows-latest
            triple: x86_64-pc-windows-msvc
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          python-version: "3.12"

      - name: Install Python dependencies (including pyinstaller)
        run: uv sync --group dev

      - name: Build sidecar binary
        run: uv run pyinstaller budget-analyser-api.spec --clean --distpath dist-sidecar

      - name: Stage binary with target triple name (Unix)
        if: runner.os != 'Windows'
        run: |
          mkdir -p src/frontend/src-tauri/binaries
          cp dist-sidecar/budget-analyser-api \
             src/frontend/src-tauri/binaries/budget-analyser-api-${{ matrix.triple }}
          chmod +x src/frontend/src-tauri/binaries/budget-analyser-api-${{ matrix.triple }}
        shell: bash

      - name: Stage binary with target triple name (Windows)
        if: runner.os == 'Windows'
        run: |
          New-Item -ItemType Directory -Force -Path src/frontend/src-tauri/binaries
          Copy-Item "dist-sidecar\budget-analyser-api.exe" `
            "src\frontend\src-tauri\binaries\budget-analyser-api-${{ matrix.triple }}.exe"
        shell: pwsh

      - name: Upload sidecar artifact
        uses: actions/upload-artifact@v4
        with:
          name: release-sidecar-${{ matrix.triple }}
          path: src/frontend/src-tauri/binaries/
          if-no-files-found: error

  build-tauri:
    needs: [version-and-tag, build-python]
    if: needs.version-and-tag.outputs.should_release == 'true'
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: windows-latest
            label: Windows
            triple: x86_64-pc-windows-msvc
          - os: macos-latest
            label: macOS_AppleSilicon
            triple: aarch64-apple-darwin
          - os: macos-13
            label: macOS_Intel
            triple: x86_64-apple-darwin
    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          python-version: "3.12"

      - name: Install Python dependencies
        run: uv sync

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22

      - name: Install frontend dependencies
        working-directory: src/frontend
        run: npm ci

      - name: Install Rust stable
        uses: dtolnay/rust-toolchain@stable

      - name: Rust cache
        uses: swatinem/rust-cache@v2
        with:
          workspaces: src/frontend/src-tauri

      - name: Download sidecar binary
        uses: actions/download-artifact@v4
        with:
          name: release-sidecar-${{ matrix.triple }}
          path: src/frontend/src-tauri/binaries/

      - name: Make sidecar executable (Unix)
        if: runner.os != 'Windows'
        run: chmod +x src/frontend/src-tauri/binaries/budget-analyser-api-${{ matrix.triple }}

      - name: Update version in tauri.conf.json
        shell: bash
        run: |
          VERSION="${{ needs.version-and-tag.outputs.version }}"
          cd src/frontend/src-tauri
          python3 -c "
          import json
          with open('tauri.conf.json', 'r') as f:
              conf = json.load(f)
          conf['version'] = '$VERSION'
          with open('tauri.conf.json', 'w') as f:
              json.dump(conf, f, indent=2)
          "

      - name: Build Tauri app and upload to release
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          projectPath: src/frontend
          tauriScript: npm run tauri
          tagName: v${{ needs.version-and-tag.outputs.version }}
          releaseName: Budget Analyser v${{ needs.version-and-tag.outputs.version }}
          releaseBody: |
            ${{ needs.version-and-tag.outputs.changelog }}

            ---

            ### Downloads
            - **Windows**: `.exe` installer
            - **macOS (Apple Silicon)**: `.dmg` for M1/M2/M3/M4 Macs
            - **macOS (Intel)**: `.dmg` for Intel Macs

            > **No Python required** — fully self-contained installer.

            > **macOS Gatekeeper**: On first launch, right-click the app → "Open" → "Open".
```

**Step 2: Commit**

```bash
git add .github/workflows/release.yml
git commit -S -m "feat(ci): add PyInstaller build jobs to release workflow

| Area                          | Change                                       |
|-------------------------------|----------------------------------------------|
| .github/workflows/release.yml | Added build-python job (ARM, Intel, Windows) |
|                               | before build-tauri; added macOS Intel build  |
|                               | target; updated release notes (no Python req)|

Author: Prabhukumar Sivamorthy"
```

---

## Task 7: Push and trigger the build-check workflow

**Step 1: Push the feature branch**

```bash
git push origin feature/update
```

**Step 2: Trigger the build-check workflow**

Navigate to:
```
https://github.com/Harvest-Forged-Code/Analyser/actions/workflows/build-check.yml
```

Click **"Run workflow"** → select branch `feature/update` → click **"Run workflow"**.

**Step 3: Monitor all 6 jobs**

Expected successful jobs:
1. `build-python (aarch64-apple-darwin)` — macOS ARM sidecar built + smoke-tested
2. `build-python (x86_64-apple-darwin)` — macOS Intel sidecar built + smoke-tested
3. `build-python (x86_64-pc-windows-msvc)` — Windows sidecar built + smoke-tested
4. `build-tauri (macOS_AppleSilicon)` — `.dmg` artifact uploaded
5. `build-tauri (macOS_Intel)` — `.dmg` artifact uploaded
6. `build-tauri (Windows)` — `.exe` artifact uploaded

**Step 4: Download and install the macOS .dmg artifact**

From the completed workflow run → Artifacts section → download `budget-analyser-macOS_AppleSilicon.dmg`.

Mount and install. Launch the app without any Python installed. Verify:
- App opens
- Data created at `~/Library/Application Support/Budget Analyser/`
- Dashboard loads

**Step 5: Commit nothing (observational step)**

If issues are found, fix them in a new commit before proceeding.
