# Build Budget Analyser Tauri app for Windows.
# Run from project root: powershell -ExecutionPolicy Bypass -File resources\scripts\build_windows.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$FrontendDir = Join-Path $ProjectRoot "src\frontend"

Write-Host "=== Budget Analyser - Windows Build ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
Write-Host ""

# --- Prerequisites check ---
Write-Host "[1/5] Checking prerequisites..." -ForegroundColor Yellow

$missing = @()

if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
    $missing += "Node.js (https://nodejs.org)"
}

if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    $missing += "uv (powershell -c 'irm https://astral.sh/uv/install.ps1 | iex')"
}

if (-not (Get-Command "rustc" -ErrorAction SilentlyContinue)) {
    $missing += "Rust (https://rustup.rs)"
}

if ($missing.Count -gt 0) {
    Write-Host "ERROR: Missing prerequisites:" -ForegroundColor Red
    foreach ($m in $missing) {
        Write-Host "  - $m" -ForegroundColor Red
    }
    exit 1
}

Write-Host "  Node.js $(node --version)"
Write-Host "  npm $(npm --version)"
Write-Host "  uv $(uv --version)"
Write-Host "  rustc $(rustc --version)"
Write-Host ""

# --- Python dependencies ---
Write-Host "[2/5] Installing Python dependencies..." -ForegroundColor Yellow
Set-Location $ProjectRoot
uv sync
Write-Host ""

# --- Frontend dependencies ---
Write-Host "[3/5] Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location $FrontendDir
npm ci
Write-Host ""

# --- Build ---
Write-Host "[4/5] Building Tauri app..." -ForegroundColor Yellow
npm run tauri build
Write-Host ""

# --- Output ---
Write-Host "[5/5] Build complete!" -ForegroundColor Green
Write-Host ""

$BundleDir = Join-Path $FrontendDir "src-tauri\target\release\bundle"

Write-Host "Artifacts:" -ForegroundColor Cyan
$msiFiles = Get-ChildItem -Path $BundleDir -Recurse -Filter "*.msi" -ErrorAction SilentlyContinue
if ($msiFiles) {
    Write-Host "  MSI:"
    foreach ($f in $msiFiles) {
        Write-Host "    $($f.FullName)"
    }
}

$exeFiles = Get-ChildItem -Path $BundleDir -Recurse -Filter "*.exe" -ErrorAction SilentlyContinue
if ($exeFiles) {
    Write-Host "  EXE:"
    foreach ($f in $exeFiles) {
        Write-Host "    $($f.FullName)"
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
