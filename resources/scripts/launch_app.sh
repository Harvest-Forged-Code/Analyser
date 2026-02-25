#!/usr/bin/env bash
# Launch the Budget Analyser desktop app (Tauri + React + FastAPI)
# Usage: ./resources/scripts/launch_app.sh
#
# This script:
#   1. Kills any existing processes on ports 8741 (API) and 5173 (Vite)
#   2. Launches the Tauri desktop app (which starts Vite + Python API)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/src/frontend"

echo "==> Stopping existing processes..."
lsof -ti :8741 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true
sleep 1

echo "==> Launching Budget Analyser from $FRONTEND_DIR"
cd "$FRONTEND_DIR"
npm run tauri dev
