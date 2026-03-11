---
name: release-build
description: Run the full build and release pipeline for the Budget Analyser desktop app
---

# Release Build Pipeline

Execute the complete build, test, and release pipeline for the Budget Analyser Tauri v2 desktop application.

## When to Use

- Before creating a release (production build)
- To verify the full build pipeline works after significant changes
- When preparing a version for distribution
- For build troubleshooting and verification

## Process

### Step 1: Pre-flight Checks

```bash
# Verify clean working tree
git status

# Check current branch
git branch --show-current

# Read version from pyproject.toml
grep 'version' pyproject.toml | head -5

# Verify dependencies are installed
uv sync --group dev
cd src/frontend && npm install
```

**Gate:** Working tree must be clean. All changes committed.

### Step 2: Backend Verification

```bash
# Ruff lint and format check
uv run ruff check src/budget_analyser/
uv run ruff format --check src/budget_analyser/

# Pylint deep analysis (score must be >= 8.0)
uv run pylint src/budget_analyser/ --score=y

# Unit tests (ALL must pass)
uv run pytest src/test/unit/ -q

# Coverage report
uv run pytest --cov=src/budget_analyser --cov-report=term-missing
```

**Gate:** All linting passes, all tests green, pylint >= 8.0.

### Step 3: Frontend Verification

```bash
cd src/frontend

# TypeScript type checking
npx tsc --noEmit

# ESLint (if configured)
npm run lint 2>/dev/null || echo "ESLint not configured, skipping"

# Vite build
npx vite build
```

**Gate:** TypeScript clean, build succeeds.

### Step 4: E2E Verification (Optional)

Prompt the user before running — E2E tests require both servers running and take longer:

```bash
cd src/frontend
npm run test:e2e
```

**Gate:** All E2E tests pass (if user chose to run them).

### Step 5: Tauri Build

```bash
cd src/frontend
npm run tauri build
```

This produces platform-specific artifacts:
- **macOS:** `src/frontend/src-tauri/target/release/bundle/dmg/*.dmg`
- **Windows:** `src/frontend/src-tauri/target/release/bundle/msi/*.msi`
- **Linux:** `src/frontend/src-tauri/target/release/bundle/appimage/*.AppImage`

**Gate:** Build completes without errors, artifacts exist.

### Step 6: Release (If Requested)

Only proceed if the user explicitly requests a release:

```bash
# Get version from pyproject.toml
VERSION=$(grep '^version' pyproject.toml | head -1 | sed 's/.*"\(.*\)"/\1/')

# Create and push git tag
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin "v$VERSION"

# Create GitHub release draft
gh release create "v$VERSION" \
  --title "Budget Analyser v$VERSION" \
  --draft \
  --generate-notes
```

### Pipeline Summary

After all steps complete, present a summary:

```markdown
## Release Build Report

| Step | Status | Details |
|------|--------|---------|
| Pre-flight | PASS/FAIL | Clean tree, branch, version |
| Ruff lint | PASS/FAIL | Error count |
| Pylint | PASS/FAIL | Score: X.X/10 |
| Unit tests | PASS/FAIL | X passed, Y failed |
| Coverage | INFO | XX% overall |
| TypeScript | PASS/FAIL | Error count |
| Frontend build | PASS/FAIL | Bundle size |
| E2E tests | PASS/FAIL/SKIPPED | X passed |
| Tauri build | PASS/FAIL | Artifact path |
| Release | CREATED/SKIPPED | Tag, URL |

**Overall: READY FOR RELEASE / ISSUES FOUND**
```

## Rules

- Never skip backend tests — they protect financial calculations
- Always run TypeScript checking — type errors in financial displays are bugs
- E2E is optional but recommended for releases
- Never auto-push tags or create releases without user confirmation
- Report all failures clearly — do not continue past a failed gate
