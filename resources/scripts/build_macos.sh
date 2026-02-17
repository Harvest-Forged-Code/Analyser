#!/usr/bin/env bash
# Build Budget Analyser Tauri app for macOS.
# Run from project root: ./resources/scripts/build_macos.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/src/frontend"

echo "=== Budget Analyser — macOS Build ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# --- Prerequisites check ---
echo "[1/5] Checking prerequisites..."

if ! command -v node &>/dev/null; then
    echo "ERROR: Node.js not found. Install via: brew install node"
    exit 1
fi

if ! command -v uv &>/dev/null; then
    echo "ERROR: uv not found. Install via: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

if ! command -v rustc &>/dev/null; then
    echo "ERROR: Rust not found. Install via: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

echo "  Node.js $(node --version)"
echo "  npm $(npm --version)"
echo "  uv $(uv --version)"
echo "  rustc $(rustc --version)"
echo ""

# --- Python dependencies ---
echo "[2/5] Installing Python dependencies..."
cd "$PROJECT_ROOT"
uv sync
echo ""

# --- Frontend dependencies ---
echo "[3/5] Installing frontend dependencies..."
cd "$FRONTEND_DIR"
npm ci
echo ""

# --- Build ---
echo "[4/5] Building Tauri app..."
npm run tauri build
echo ""

# --- Output ---
echo "[5/5] Build complete!"
echo ""
echo "Artifacts:"
BUNDLE_DIR="$FRONTEND_DIR/src-tauri/target/release/bundle"
if [ -d "$BUNDLE_DIR/dmg" ]; then
    echo "  DMG:"
    find "$BUNDLE_DIR/dmg" -name "*.dmg" -exec echo "    {}" \;
fi
if [ -d "$BUNDLE_DIR/macos" ]; then
    echo "  App:"
    find "$BUNDLE_DIR/macos" -name "*.app" -maxdepth 1 -exec echo "    {}" \;
fi
echo ""
echo "Done."
