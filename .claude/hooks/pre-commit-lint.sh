#!/bin/bash
# Hook: pre-commit-lint
# Event: PreToolUse (Bash)
# Purpose: Run ruff lint and format check on staged Python files BEFORE git commit executes
#          Blocks the commit if linting fails.

# Read the tool input from stdin
INPUT=$(cat)

# Extract the command
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

# Get the project root (where .git is)
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$GIT_ROOT" ]; then
  exit 0
fi

# Get staged Python files
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM -- '*.py' 2>/dev/null)

if [ -z "$STAGED_PY_FILES" ]; then
  # No Python files staged, allow commit
  exit 0
fi

echo "🔍 Pre-commit lint check: Running ruff on staged Python files..."

# Check if ruff is available
if ! command -v ruff &> /dev/null; then
  echo "⚠️  ruff not found. Install with: pip install ruff"
  echo "   Skipping lint check."
  exit 0
fi

# Run ruff check on staged files
LINT_FAILED=false

for file in $STAGED_PY_FILES; do
  if [ -f "$GIT_ROOT/$file" ]; then
    # Run lint check
    LINT_OUTPUT=$(ruff check "$GIT_ROOT/$file" 2>&1)
    if [ $? -ne 0 ]; then
      if [ "$LINT_FAILED" = false ]; then
        echo ""
        echo "❌ LINT ERRORS FOUND — commit blocked until fixed:"
        echo "───────────────────────────────────────────────────"
        LINT_FAILED=true
      fi
      echo "$LINT_OUTPUT"
    fi

    # Run format check
    FORMAT_OUTPUT=$(ruff format --check "$GIT_ROOT/$file" 2>&1)
    if [ $? -ne 0 ]; then
      if [ "$LINT_FAILED" = false ]; then
        echo ""
        echo "❌ FORMAT ERRORS FOUND — commit blocked until fixed:"
        echo "───────────────────────────────────────────────────"
        LINT_FAILED=true
      fi
      echo "  $file needs formatting: run 'ruff format $file'"
    fi
  fi
done

if [ "$LINT_FAILED" = true ]; then
  echo ""
  echo "───────────────────────────────────────────────────"
  echo "💡 Fix with: ruff check --fix . && ruff format ."
  echo "   Then re-stage and commit."
  echo ""
  echo "BLOCKING: Commit will not proceed until lint passes."
  # Exit with error to block the commit
  exit 1
fi

echo "✅ All staged Python files pass lint and format checks."
exit 0
