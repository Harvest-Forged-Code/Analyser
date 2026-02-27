# Sidecar Bundling Design

**Date:** 2026-02-26
**Status:** Approved
**Approach:** PyInstaller sidecar

## Goal

Make Budget Analyser a true standalone desktop app — no Python, uv, or project checkout required. Install the `.dmg` or `.exe` and it works.

## Architecture

```
Budget Analyser.app (or .exe)
├── Tauri shell (Rust binary)         ← frontend + app lifecycle
├── React UI (bundled into binary)    ← HTML/JS/CSS
└── budget-analyser-api (sidecar)     ← PyInstaller-frozen Python binary
        └── FastAPI + uvicorn + all Python deps frozen inside
```

### Launch sequence

1. Tauri starts
2. Tauri resolves `BUDGET_ANALYSER_DATA_DIR` (OS standard location) and sets it as an env var
3. Tauri spawns the sidecar (`budget-analyser-api`)
4. Sidecar reads `BUDGET_ANALYSER_DATA_DIR`, seeds defaults on first launch, starts uvicorn on port 8741
5. Tauri polls `http://127.0.0.1:8741/api/health` until ready (20 retries × 500 ms)
6. React frontend loads and makes REST calls as before — no API changes

### User data location

| Platform | Path |
|---|---|
| macOS | `~/Library/Application Support/Budget Analyser/` |
| Windows | `%APPDATA%\Budget Analyser\` |

Contains: `budget_analyser.db`, `mappers/*.json`, `config/`, `statements/`

## Components Changed

### 1. `budget-analyser-api.spec` (new, project root)

PyInstaller spec file:
- Entry point: `src/budget_analyser/api/main.py`
- Bundles `src/budget_analyser/data/` as seed data (read-only assets)
- One-file mode: `False` (one-dir is more reliable with pandas/numpy)
- Output binary name: `budget-analyser-api`

### 2. `src/budget_analyser/settings/settings.py`

- Read `BUDGET_ANALYSER_DATA_DIR` env var to resolve the data root
- Fall back to `src/budget_analyser/data/` when env var is absent (dev mode unchanged)
- On first launch: copy bundled seed data to data dir if it does not exist

### 3. `src/frontend/src-tauri/src/lib.rs`

- Replace manual `Command::new(python)` with Tauri sidecar API
- Set `BUDGET_ANALYSER_DATA_DIR` env var before spawning
- Dev mode fallback: if sidecar binary not found, fall back to `.venv/bin/python` (preserves `npm run tauri dev` workflow)

### 4. `src/frontend/src-tauri/tauri.conf.json`

```json
"bundle": {
  "externalBin": ["binaries/budget-analyser-api"]
}
```

### 5. CI workflows (`release.yml` + `build-check.yml`)

Add PyInstaller build step before Tauri build on each platform.

macOS requires two separate jobs (ARM + Intel):

```
build-python-arm   (macos-latest) → budget-analyser-api-aarch64-apple-darwin
build-python-intel (macos-13)     → budget-analyser-api-x86_64-apple-darwin
build-tauri-macos  (macos-latest) ← consumes both → .dmg

build-python-windows (windows-latest) → budget-analyser-api-x86_64-pc-windows-msvc.exe
build-tauri-windows  (windows-latest) ← consumes it → .exe installer
```

Binaries are passed between jobs via `actions/upload-artifact` / `actions/download-artifact`.

## First-Launch Seeding

PyInstaller bundles `data/` as read-only assets inside the frozen package.

On startup the Python backend:
1. Checks if `BUDGET_ANALYSER_DATA_DIR` exists and has `mappers/` and `config/`
2. If not: copies bundled seed files there, creates empty `budget_analyser.db`
3. If yes: skips — existing user data is never overwritten

On app update: only new seed files added; existing user data untouched.

## Error Handling

| Scenario | Behaviour |
|---|---|
| Sidecar binary missing | Tauri error dialog: "App installation is corrupted, please reinstall" |
| Sidecar crashes on startup | Health check fails after 10 s → error dialog: "Backend failed to start" |
| Data dir not writable | Python logs error; API returns 503 with clear message |
| Port 8741 already in use | Sidecar exits; Tauri health check fails → error dialog |
| App update installed | Data dir untouched; new seed files added only |

## Dev Mode Preserved

`npm run tauri dev` continues to work — `lib.rs` falls back to `.venv/bin/python` when the sidecar binary is absent. No PyInstaller build required for day-to-day development.

## Testing

| Test | Type | Validates |
|---|---|---|
| PyInstaller smoke test | CI | Frozen binary starts, `/api/health` returns 200, exits cleanly |
| First-launch seeding | Unit | Data dir created with correct structure in empty temp dir |
| Data path resolution | Unit | Env var read correctly; dev fallback works |
| Clean-machine install | Manual | `.dmg`/`.exe` on machine with no Python — app launches and works |
| Update simulation | Manual | v1 data intact after v2 install |
| Port conflict | Manual | Second instance shows error dialog |

All 469 existing unit tests pass unchanged.

## Platforms

| Platform | Runner | Output |
|---|---|---|
| macOS Apple Silicon | `macos-latest` | `.dmg` (aarch64) |
| macOS Intel | `macos-13` | `.dmg` (x86_64) |
| Windows | `windows-latest` | `.exe` NSIS installer |
