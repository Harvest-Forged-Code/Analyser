#!/bin/bash
# Hook: type-check
# Event: PreToolUse (Bash)
# Purpose: Block commits if type checking fails on staged Python files

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

# Get staged Python files
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM -- '*.py' 2>/dev/null)

if [ -z "$STAGED_PY_FILES" ]; then
  exit 0
fi

echo "🔍 Type check: Running pyright on staged Python files..."

# Try pyright first
if uv run pyright --version &> /dev/null 2>&1; then
  TYPE_OUTPUT=$(uv run pyright $STAGED_PY_FILES 2>&1)
  TYPE_EXIT=$?

  if [ $TYPE_EXIT -ne 0 ]; then
    ERROR_COUNT=$(echo "$TYPE_OUTPUT" | grep -oE '[0-9]+ error' | grep -oE '[0-9]+' | head -1)
    echo ""
    echo "❌ TYPE ERRORS FOUND — commit blocked"
    echo "───────────────────────────────────────────────────"
    echo "$TYPE_OUTPUT" | grep -E '(error|Error)' | head -15
    echo ""
    echo "───────────────────────────────────────────────────"
    echo "💡 Fix type errors: uv run pyright"
    echo ""
    echo "BLOCKING: Commit will not proceed until type errors are resolved."
    exit 1
  fi

  echo "✅ Type checking passed (pyright)."
  exit 0
fi

# Fallback to mypy
if uv run mypy --version &> /dev/null 2>&1; then
  echo "   (pyright not found, using mypy fallback)"
  TYPE_OUTPUT=$(uv run mypy $STAGED_PY_FILES 2>&1)
  TYPE_EXIT=$?

  if [ $TYPE_EXIT -ne 0 ]; then
    echo ""
    echo "❌ TYPE ERRORS FOUND — commit blocked"
    echo "───────────────────────────────────────────────────"
    echo "$TYPE_OUTPUT" | grep -E '(error|Error)' | head -15
    echo ""
    echo "───────────────────────────────────────────────────"
    echo "💡 Fix type errors: uv run mypy src/"
    echo ""
    echo "BLOCKING: Commit will not proceed until type errors are resolved."
    exit 1
  fi

  echo "✅ Type checking passed (mypy)."
  exit 0
fi

# Neither available
echo "⚠️  Neither pyright nor mypy available. Skipping type check."
exit 0
