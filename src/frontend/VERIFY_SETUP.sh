#!/bin/bash
# Tauri v2 Setup Verification Script
# Run this from: /Users/Prabhukumar/Projects/PycharmProjects/Analyser/frontend

set -e  # Exit on error

echo "========================================="
echo "Budget Analyser - Tauri v2 Verification"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Rust
echo "Step 1: Checking Rust installation..."
source "$HOME/.cargo/env"
if command -v rustc &> /dev/null; then
    RUST_VERSION=$(rustc --version)
    echo -e "${GREEN}✓${NC} Rust found: $RUST_VERSION"
else
    echo -e "${RED}✗${NC} Rust not found. Install from https://rustup.rs/"
    exit 1
fi

if command -v cargo &> /dev/null; then
    CARGO_VERSION=$(cargo --version)
    echo -e "${GREEN}✓${NC} Cargo found: $CARGO_VERSION"
else
    echo -e "${RED}✗${NC} Cargo not found"
    exit 1
fi
echo ""

# Step 2: Check Node.js
echo "Step 2: Checking Node.js installation..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js found: $NODE_VERSION"
else
    echo -e "${RED}✗${NC} Node.js not found"
    exit 1
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓${NC} npm found: v$NPM_VERSION"
else
    echo -e "${RED}✗${NC} npm not found"
    exit 1
fi
echo ""

# Step 3: Check src-tauri files
echo "Step 3: Verifying Tauri configuration files..."
REQUIRED_FILES=(
    "src-tauri/Cargo.toml"
    "src-tauri/build.rs"
    "src-tauri/tauri.conf.json"
    "src-tauri/src/main.rs"
    "src-tauri/src/lib.rs"
    "src-tauri/capabilities/default.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} Found: $file"
    else
        echo -e "${RED}✗${NC} Missing: $file"
        exit 1
    fi
done
echo ""

# Step 4: Check node_modules
echo "Step 4: Checking npm dependencies..."
if [ -d "node_modules" ]; then
    echo -e "${GREEN}✓${NC} node_modules exists"

    if [ -d "node_modules/@tauri-apps/cli" ]; then
        echo -e "${GREEN}✓${NC} @tauri-apps/cli installed"
    else
        echo -e "${YELLOW}!${NC} @tauri-apps/cli not found, installing..."
        npm install
    fi
else
    echo -e "${YELLOW}!${NC} node_modules not found, installing..."
    npm install
fi
echo ""

# Step 5: Compile Rust code
echo "Step 5: Compiling Tauri Rust code (this may take a while on first run)..."
echo "Running: cargo check --manifest-path src-tauri/Cargo.toml"
echo ""

if cargo check --manifest-path src-tauri/Cargo.toml; then
    echo ""
    echo -e "${GREEN}✓${NC} Rust compilation successful!"
else
    echo ""
    echo -e "${RED}✗${NC} Rust compilation failed. Check errors above."
    exit 1
fi
echo ""

# Step 6: Verify Python API exists
echo "Step 6: Checking Python API..."
if [ -f "../src/budget_analyser/api/main.py" ]; then
    echo -e "${GREEN}✓${NC} Python API found: ../src/budget_analyser/api/main.py"
else
    echo -e "${YELLOW}!${NC} Python API not found at expected location"
    echo "    Expected: /Users/Prabhukumar/Projects/PycharmProjects/Analyser/src/budget_analyser/api/main.py"
fi
echo ""

# Summary
echo "========================================="
echo -e "${GREEN}VERIFICATION COMPLETE!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Test Tauri dev mode:"
echo "     npm run tauri:dev"
echo ""
echo "  2. Or start manually:"
echo "     Terminal 1: cd .. && python -m budget_analyser.api.main"
echo "     Terminal 2: npm run tauri:dev"
echo ""
echo "  3. Build production app:"
echo "     npm run tauri:build"
echo ""
echo "See TAURI_SETUP.md for detailed documentation."
echo ""
