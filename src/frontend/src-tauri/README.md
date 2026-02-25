# Tauri v2 Sidecar Configuration

This directory contains the Tauri v2 desktop application wrapper for Budget Analyser.

## Architecture

The Tauri app acts as a **sidecar** that:
1. Launches the Python FastAPI backend on startup (`budget_analyser.api.main`)
2. Serves the React frontend from Vite
3. Manages the Python process lifecycle
4. Handles desktop window management
5. Terminates the Python process when the window closes

## Project Structure

```
src-tauri/
├── Cargo.toml              # Rust dependencies (Tauri 2, reqwest, serde)
├── build.rs                # Tauri build script
├── tauri.conf.json         # Tauri configuration (window size, permissions, build)
├── capabilities/
│   └── default.json        # Tauri permissions manifest
├── src/
│   ├── lib.rs              # Main sidecar logic (Python API lifecycle)
│   └── main.rs             # Entry point
└── icons/                  # Application icons (placeholder)
```

## Key Features

### Python API Sidecar (`src/lib.rs`)

- **Startup**: Spawns `python -m budget_analyser.api.main` as a child process
- **Health Check**: Retries `http://127.0.0.1:8741/api/health` up to 10 times (500ms intervals)
- **Lifecycle**: Stores child process in Tauri state (`ApiProcess`)
- **Cleanup**: Kills Python process on window close event

### Configuration (`tauri.conf.json`)

- **Window**: 1280x800 (min 1024x768), centered
- **Dev Server**: Vite on `http://localhost:5173`
- **Build**: Outputs to `../dist`
- **Permissions**: Shell plugin enabled for opening external links

## Development

### First-Time Setup

1. **Install Rust** (already done):
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source "$HOME/.cargo/env"
   ```

2. **Verify Tauri compiles**:
   ```bash
   cd /Users/Prabhukumar/Projects/PycharmProjects/Analyser/frontend
   source "$HOME/.cargo/env"
   cargo check --manifest-path src-tauri/Cargo.toml
   ```

3. **Install frontend dependencies** (if not done):
   ```bash
   npm install
   ```

### Running the App

**Development mode** (hot reload):
```bash
# Terminal 1: Start Python API manually (or let Tauri start it)
cd /Users/Prabhukumar/Projects/PycharmProjects/Analyser
python -m budget_analyser.api.main

# Terminal 2: Start Tauri dev
cd frontend
npm run tauri dev
```

**Alternative** (let Tauri handle everything):
```bash
cd frontend
npm run tauri dev
# Tauri will auto-start Python API and Vite
```

### Building for Production

```bash
cd frontend
npm run tauri build
```

This will:
1. Run `npm run build` (Vite production build)
2. Compile Rust binary
3. Bundle Python API (if configured)
4. Create platform-specific installers in `src-tauri/target/release/bundle/`

## Dependencies

### Rust Crates
- `tauri` v2: Desktop app framework
- `tauri-plugin-shell` v2: Shell/process management
- `reqwest` v0.12: HTTP client (with blocking for health checks)
- `serde` v1: JSON serialization
- `tokio` v1: Async runtime

### Python Backend
- FastAPI app running on `http://127.0.0.1:8741`
- Endpoints: `/api/health`, `/api/statements/*`, etc.

## Troubleshooting

### Python API not starting
- Ensure Python environment is active: `source venv/bin/activate`
- Check Python API runs standalone: `python -m budget_analyser.api.main`
- Verify port 8741 is free: `lsof -i :8741`

### Rust compilation errors
- Update Rust: `rustup update`
- Clean build: `cargo clean --manifest-path src-tauri/Cargo.toml`
- Check Cargo.toml versions match Tauri v2 requirements

### Icon errors
- Icons are currently placeholders
- Generate proper icons: `npm run tauri icon /path/to/icon.png`

### Window not opening
- Check console for Tauri errors
- Verify Vite dev server is running on port 5173
- Check `tauri.conf.json` devUrl matches Vite port

## Next Steps

1. **Add application icons**: Create 1024x1024 PNG and run `npm run tauri icon`
2. **Bundle Python**: Configure Tauri to bundle Python interpreter for production
3. **Code signing**: Set up certificates for macOS/Windows distribution
4. **Auto-updater**: Configure Tauri updater plugin for seamless updates
5. **System tray**: Add system tray icon for background operation

## Resources

- [Tauri v2 Docs](https://v2.tauri.app/)
- [Tauri Sidecar Guide](https://v2.tauri.app/develop/sidecar/)
- [Tauri Rust API](https://docs.rs/tauri/2.0.0/)
