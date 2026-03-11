#!/bin/bash
# Hook: frontend-lint
# Event: PreToolUse (Bash)
# Purpose: Block commits if frontend TypeScript/ESLint checks fail

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | grep -oE '"command"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Only intercept git commit commands
case "$COMMAND" in
  *"git commit"*)
    ;;
  *)
    exit 0
    ;;
esac

GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$GIT_ROOT" ]; then
  exit 0
fi

# Get staged frontend files
STAGED_FE_FILES=$(git diff --cached --name-only --diff-filter=ACM -- 'src/frontend/src/**/*.ts' 'src/frontend/src/**/*.tsx' 'src/frontend/src/**/*.js' 'src/frontend/src/**/*.jsx' 2>/dev/null)

if [ -z "$STAGED_FE_FILES" ]; then
  exit 0
fi

FRONTEND_DIR="$GIT_ROOT/src/frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
  exit 0
fi

echo "🔍 Frontend lint: Checking staged TypeScript/JS files..."

LINT_FAILED=false

# TypeScript check
if [ -f "$FRONTEND_DIR/tsconfig.json" ]; then
  TSC_OUTPUT=$(cd "$FRONTEND_DIR" && npx tsc --noEmit 2>&1)
  TSC_EXIT=$?

  if [ $TSC_EXIT -ne 0 ]; then
    LINT_FAILED=true
    ERROR_COUNT=$(echo "$TSC_OUTPUT" | grep -c 'error TS')
    echo ""
    echo "❌ TYPESCRIPT ERRORS FOUND ($ERROR_COUNT errors)"
    echo "───────────────────────────────────────────────────"
    echo "$TSC_OUTPUT" | grep 'error TS' | head -10
    echo ""
  fi
fi

# ESLint check (if configured)
if [ -f "$FRONTEND_DIR/.eslintrc.json" ] || [ -f "$FRONTEND_DIR/.eslintrc.js" ] || [ -f "$FRONTEND_DIR/eslint.config.js" ] || [ -f "$FRONTEND_DIR/eslint.config.mjs" ]; then
  ESLINT_OUTPUT=$(cd "$FRONTEND_DIR" && npx eslint src/ --max-warnings 0 2>&1)
  ESLINT_EXIT=$?

  if [ $ESLINT_EXIT -ne 0 ]; then
    LINT_FAILED=true
    echo "❌ ESLINT ERRORS FOUND"
    echo "───────────────────────────────────────────────────"
    echo "$ESLINT_OUTPUT" | head -15
    echo ""
  fi
fi

if [ "$LINT_FAILED" = true ]; then
  echo "───────────────────────────────────────────────────"
  echo "💡 Fix TypeScript: cd src/frontend && npx tsc --noEmit"
  echo "   Fix ESLint:     cd src/frontend && npx eslint src/ --fix"
  echo ""
  echo "BLOCKING: Commit will not proceed until frontend checks pass."
  exit 1
fi

echo "✅ Frontend TypeScript and lint checks passed."
exit 0
