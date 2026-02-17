# Tauri v2 Sidecar Setup Guide

This guide walks through the complete Tauri v2 desktop application setup for Budget Analyser.

## What Was Created

The following Tauri configuration has been set up:

```
frontend/
├── src-tauri/
│   ├── Cargo.toml              # Rust dependencies (Tauri 2.10)
│   ├── build.rs                # Tauri build configuration
│   ├── tauri.conf.json         # App config (window, permissions, build)
│   ├── capabilities/
│   │   └── default.json        # Permission manifest
│   ├── src/
│   │   ├── lib.rs              # Python API sidecar lifecycle management
│   │   └── main.rs             # Application entry point
│   ├── icons/
│   │   └── README.md           # Icon placeholder instructions
│   └── README.md               # Detailed Tauri documentation
├── .gitignore                  # Added src-tauri/target/
└── package.json                # Updated with tauri:dev, tauri:build scripts
```

## Architecture Overview

**Tauri Sidecar Pattern:**

1. **User launches desktop app** → Tauri window opens
2. **Tauri spawns Python process** → `python -m budget_analyser.api.main`
3. **Health check retries** → Waits for FastAPI to start (10 retries, 500ms intervals)
4. **React frontend loads** → Served from Vite (dev) or bundled dist (prod)
5. **User interacts with UI** → React calls FastAPI endpoints via axios
6. **User closes window** → Tauri kills Python process gracefully

## Verification Steps

### 1. Verify Rust Environment

```bash
source "$HOME/.cargo/env"
rustc --version
cargo --version
```

Expected output:
```
rustc 1.93.1 (or later)
cargo 1.93.1 (or later)
```

### 2. Compile Tauri Configuration

From the `frontend/` directory:

```bash
cd /Users/Prabhukumar/Projects/PycharmProjects/Analyser/frontend
source "$HOME/.cargo/env"
cargo check --manifest-path src-tauri/Cargo.toml
```

**Expected output:**
- First run: Downloads Tauri crates (takes 2-5 minutes)
- Final line: `Finished 'dev' profile [unoptimized + debuginfo] target(s) in X.XXs`

**If errors occur:**
- Icon errors: Ignore for now (icons are placeholders)
- Dependency errors: Check `Cargo.toml` versions match Tauri v2
- Compilation errors: Review `src-tauri/src/lib.rs` syntax

### 3. Test Tauri Dev Mode

**Option A: Let Tauri start everything (recommended for testing sidecar)**

```bash
cd /Users/Prabhukumar/Projects/PycharmProjects/Analyser/frontend
npm run tauri:dev
```

This will:
1. Compile Rust code (first run takes 5-10 minutes)
2. Start Python API via sidecar (`python -m budget_analyser.api.main`)
3. Start Vite dev server on port 5173
4. Open Tauri desktop window

**Option B: Manual Python API (recommended for development)**

```bash
# Terminal 1: Start Python API manually
cd /Users/Prabhukumar/Projects/PycharmProjects/Analyser
source venv/bin/activate  # Activate your Python venv
python -m budget_analyser.api.main

# Terminal 2: Start Tauri (will detect already-running API)
cd frontend
npm run tauri:dev
```

**Success indicators:**
- Desktop window opens (1280x800)
- Console shows: "Python API health check succeeded"
- React app loads in the window
- Network requests to `http://127.0.0.1:8741/api/*` work

### 4. Build Production App

```bash
cd /Users/Prabhukumar/Projects/PycharmProjects/Analyser/frontend
npm run tauri:build
```

**Build outputs:**
- macOS: `src-tauri/target/release/bundle/macos/Budget Analyser.app`
- DMG: `src-tauri/target/release/bundle/dmg/Budget Analyser_1.0.0_x64.dmg`

**Note:** Production builds require:
- Bundling Python interpreter (not yet configured)
- Code signing certificates (for macOS distribution)
- See "Next Steps" section below

## Configuration Details

### Window Configuration (`tauri.conf.json`)

```json
{
  "app": {
    "windows": [{
      "title": "Budget Analyser",
      "width": 1280,
      "height": 800,
      "minWidth": 1024,
      "minHeight": 768,
      "center": true
    }]
  }
}
```

### Python API Sidecar (`src-tauri/src/lib.rs`)

**Startup logic:**
```rust
fn start_python_api() -> Option<Child> {
    Command::new("python")
        .args(["-m", "budget_analyser.api.main"])
        .spawn()
        .ok()
}
```

**Health check:**
```rust
fn check_api_health() -> bool {
    reqwest::blocking::get("http://127.0.0.1:8741/api/health")
        .ok()
        .map(|r| r.status().is_success())
        .unwrap_or(false)
}
```

**Cleanup on window close:**
```rust
.on_window_event(|window, event| {
    if let tauri::WindowEvent::Destroyed = event {
        // Kills Python process stored in ApiProcess state
    }
})
```

### Rust Dependencies (`Cargo.toml`)

| Crate | Version | Purpose |
|-------|---------|---------|
| `tauri` | 2.x | Desktop app framework |
| `tauri-plugin-shell` | 2.x | Process/shell management |
| `reqwest` | 0.12 | HTTP client (blocking + async) |
| `serde` | 1.x | JSON serialization |
| `tokio` | 1.x | Async runtime |

## Troubleshooting

### Issue: "Python API health check failed"

**Diagnosis:**
```bash
# Check if Python API is running
lsof -i :8741

# Check Python API logs
cd /Users/Prabhukumar/Projects/PycharmProjects/Analyser
python -m budget_analyser.api.main
# Look for startup errors
```

**Solutions:**
1. Ensure Python environment is activated
2. Verify port 8741 is free
3. Check Python dependencies are installed: `pip install -r requirements.txt`
4. Review FastAPI logs for errors

### Issue: Rust compilation errors

**Solution 1: Update Rust toolchain**
```bash
rustup update
```

**Solution 2: Clean and rebuild**
```bash
cargo clean --manifest-path src-tauri/Cargo.toml
cargo check --manifest-path src-tauri/Cargo.toml
```

**Solution 3: Check Tauri CLI version**
```bash
npm list @tauri-apps/cli
# Should be 2.10.0 or later
```

### Issue: Window opens but shows blank screen

**Diagnosis:**
- Open DevTools: Right-click → Inspect Element
- Check Console for errors
- Verify Vite dev server is running: `http://localhost:5173`

**Solutions:**
1. Check `tauri.conf.json` devUrl matches Vite port
2. Verify `vite.config.ts` has correct Tauri settings
3. Clear Vite cache: `rm -rf node_modules/.vite`

### Issue: Icons missing

**Solution:**
Icons are currently placeholders. To add proper icons:

```bash
# 1. Create a 1024x1024 PNG icon
# 2. Generate all icon sizes
npm run tauri:icon /path/to/your/icon.png
```

## Next Steps

### 1. Bundle Python for Production

Current sidecar assumes Python is installed on user's system. For production:

**Option A: Use PyInstaller binary**
- Build standalone Python binary: `pyinstaller --onefile budget_analyser/api/main.py`
- Configure Tauri to bundle binary as sidecar
- Update `lib.rs` to call bundled binary instead of `python -m`

**Option B: Bundle Python interpreter**
- Use `py2app` (macOS) or `PyOxidizer`
- Package entire Python runtime with app
- Larger app size but guaranteed compatibility

### 2. Add Application Icons

```bash
# Install icon generator (if not in package.json)
npm install --save-dev @tauri-apps/cli

# Generate icons from source PNG
npm run tauri:icon assets/icon.png
```

This creates all required icon sizes for macOS/Windows/Linux.

### 3. Configure Code Signing (macOS)

For macOS distribution outside App Store:

```bash
# 1. Get Apple Developer ID certificate
# 2. Add to tauri.conf.json:
{
  "bundle": {
    "macOS": {
      "signingIdentity": "Developer ID Application: Your Name (TEAMID)"
    }
  }
}
```

### 4. Enable Auto-Updates

```bash
# Install updater plugin
npm install @tauri-apps/plugin-updater

# Configure in tauri.conf.json
{
  "plugins": {
    "updater": {
      "endpoints": ["https://your-update-server.com/updates/{{target}}/{{current_version}}"]
    }
  }
}
```

### 5. Add System Tray Icon

For background operation:

```rust
// In lib.rs
use tauri::SystemTray;

tauri::Builder::default()
    .system_tray(SystemTray::new())
    .on_system_tray_event(|app, event| {
        // Handle tray clicks
    })
```

## Development Workflow

### Daily Development

```bash
# Option 1: Let Tauri handle everything
npm run tauri:dev

# Option 2: Manual control (recommended)
# Terminal 1: Python API
python -m budget_analyser.api.main

# Terminal 2: Tauri dev
npm run tauri:dev
```

### Testing Production Build

```bash
# Build the app
npm run tauri:build

# Run built app (macOS)
open src-tauri/target/release/bundle/macos/Budget\ Analyser.app
```

### Debugging

**Rust side:**
```bash
# Enable debug logging
RUST_LOG=debug npm run tauri:dev
```

**Frontend side:**
- Open DevTools in Tauri window: Right-click → Inspect Element
- Console logs appear in Tauri terminal

**Python side:**
- Check stdout/stderr from sidecar process
- Add logging to FastAPI endpoints

## Resources

- **Tauri v2 Docs**: https://v2.tauri.app/
- **Tauri Sidecar Guide**: https://v2.tauri.app/develop/sidecar/
- **Rust Tauri API**: https://docs.rs/tauri/2.0.0/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

## Summary

You now have a complete Tauri v2 desktop application that:
- ✅ Launches Python FastAPI backend as sidecar process
- ✅ Serves React frontend from Vite (dev) or bundled files (prod)
- ✅ Manages Python process lifecycle (start on launch, kill on close)
- ✅ Health checks to ensure API is ready before loading UI
- ✅ Cross-platform support (macOS, Windows, Linux)

**Verification checklist:**
- [ ] `cargo check --manifest-path src-tauri/Cargo.toml` passes
- [ ] `npm run tauri:dev` opens desktop window
- [ ] Python API starts and health check succeeds
- [ ] React frontend loads in Tauri window
- [ ] API calls work (check Network tab in DevTools)
- [ ] Python process terminates when window closes

**Production readiness:**
- [ ] Bundle Python interpreter/binary
- [ ] Add application icons
- [ ] Configure code signing
- [ ] Set up auto-updater
- [ ] Create installers (DMG, MSI, AppImage)
