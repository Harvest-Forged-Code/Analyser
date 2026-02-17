# Tauri Quick Start

**Goal**: Get the Budget Analyser desktop app running in under 5 minutes.

## Prerequisites

- ✅ Rust installed (cargo 1.93.1, rustc 1.93.1)
- ✅ Node.js and npm installed
- ✅ Frontend scaffold exists (`package.json`, `vite.config.ts`)
- ✅ Tauri configuration created (`src-tauri/` directory)

## Quick Start

### Step 1: Verify Setup (30 seconds)

```bash
cd /Users/Prabhukumar/Projects/PycharmProjects/Analyser/frontend
source "$HOME/.cargo/env"
chmod +x VERIFY_SETUP.sh
./VERIFY_SETUP.sh
```

**Expected output**: All checkmarks, final message "VERIFICATION COMPLETE!"

### Step 2: First-Time Compile (5-10 minutes)

```bash
# This downloads Tauri dependencies and compiles Rust code
npm run tauri:dev
```

**What happens**:
1. Cargo downloads ~200 crates (one-time, takes 2-5 minutes)
2. Rust compiles Tauri app (takes 3-5 minutes on first run)
3. Tauri spawns Python API: `python -m budget_analyser.api.main`
4. Tauri starts Vite dev server on port 5173
5. Desktop window opens with React app

**If it works**: Desktop window appears, React app loads. Done!

**If it fails**: See "Troubleshooting" section below.

### Step 3: Development Workflow (subsequent runs)

Once compiled, dev mode starts in ~30 seconds:

```bash
npm run tauri:dev
```

**Hot reload**: Changes to React code reload instantly. Changes to Rust code require recompilation.

## Alternative: Manual Control

For debugging or when you want more control:

```bash
# Terminal 1: Start Python API manually
cd /Users/Prabhukumar/Projects/PycharmProjects/Analyser
source venv/bin/activate  # Your Python virtualenv
python -m budget_analyser.api.main

# Terminal 2: Start Tauri (will detect running API)
cd frontend
npm run tauri:dev
```

**Benefit**: See Python logs directly, easier to debug API issues.

## Troubleshooting

### Error: "Python API health check failed"

**Cause**: Python API not running on port 8741.

**Fix**:
```bash
# Check if port is in use
lsof -i :8741

# Start API manually to see errors
cd /Users/Prabhukumar/Projects/PycharmProjects/Analyser
python -m budget_analyser.api.main
# Look for errors in output
```

Common causes:
- Python environment not activated
- Missing dependencies: `pip install -r requirements.txt`
- Port 8741 already in use

### Error: "cargo: command not found"

**Cause**: Rust environment not loaded.

**Fix**:
```bash
source "$HOME/.cargo/env"
# Then retry: npm run tauri:dev
```

### Error: Icon warnings

**Cause**: Placeholder icons not yet generated.

**Fix**: Ignore for now, or generate icons:
```bash
# Create a 1024x1024 PNG icon first
npm run tauri:icon /path/to/icon.png
```

### Window opens but blank screen

**Cause**: Vite dev server not starting, or API not responding.

**Fix**:
1. Open DevTools: Right-click window → Inspect Element
2. Check Console for errors
3. Verify Vite is running: `http://localhost:5173` in browser
4. Check Network tab for failed API calls

### Compilation errors

**Fix**:
```bash
# Update Rust
rustup update

# Clean and rebuild
cd /Users/Prabhukumar/Projects/PycharmProjects/Analyser/frontend
cargo clean --manifest-path src-tauri/Cargo.toml
npm run tauri:dev
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `npm run tauri:dev` | Start development mode |
| `npm run tauri:build` | Build production app |
| `npm run tauri:icon <path>` | Generate icons from PNG |
| `cargo check --manifest-path src-tauri/Cargo.toml` | Check Rust code |
| `cargo clean --manifest-path src-tauri/Cargo.toml` | Clean Rust build |

## Success Indicators

When everything works, you'll see:

**Terminal output**:
```
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 1.23s
[INFO] Starting Python API...
[INFO] Health check succeeded
[INFO] Starting Vite dev server...
```

**Desktop window**:
- 1280x800 window titled "Budget Analyser"
- React app loads (Dashboard or Login page)
- No console errors in DevTools

**Process check**:
```bash
ps aux | grep budget_analyser
# Should show: python -m budget_analyser.api.main
```

## What's Next?

Once the app runs successfully:

1. **Explore the UI**: React app should be fully functional
2. **Test API calls**: Open Network tab, verify endpoints work
3. **Make changes**: Edit React code, see hot reload
4. **Check lifecycle**: Close window, verify Python process terminates

For detailed information:
- Architecture: `src-tauri/README.md`
- Full setup guide: `TAURI_SETUP.md`
- File inventory: `TAURI_FILES_CREATED.md`

## Time Estimates

| Task | First Time | Subsequent |
|------|------------|------------|
| Rust compilation | 5-10 min | 30-60 sec |
| Python API startup | 2-3 sec | 2-3 sec |
| Vite dev server | 3-5 sec | 3-5 sec |
| **Total dev mode start** | **~10 min** | **~45 sec** |

Production build: ~10-15 minutes (includes optimizations)

## Production Build

When ready to create a distributable app:

```bash
npm run tauri:build
```

**Output location**:
- macOS: `src-tauri/target/release/bundle/macos/Budget Analyser.app`
- DMG: `src-tauri/target/release/bundle/dmg/Budget Analyser_1.0.0_x64.dmg`

**Note**: Production builds currently require Python on user's system. See "Bundling Python" section in `TAURI_SETUP.md` for standalone distribution.

## Need Help?

1. Run verification script: `./VERIFY_SETUP.sh`
2. Check troubleshooting: `TAURI_SETUP.md` (search for your error)
3. Review Rust logs: Check terminal output for compilation errors
4. Review Python logs: Start API manually to see FastAPI errors
5. Check Tauri docs: https://v2.tauri.app/

---

**Ready?** Run `npm run tauri:dev` and watch the magic happen!
