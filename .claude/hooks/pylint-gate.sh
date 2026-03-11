#!/bin/bash
# Hook: pylint-gate
# Event: PreToolUse (Bash)
# Purpose: Block commits if pylint score drops below 8.0/10

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

# Get staged Python files under src/budget_analyser/
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM -- 'src/budget_analyser/**/*.py' 2>/dev/null)

if [ -z "$STAGED_PY_FILES" ]; then
  exit 0
fi

echo "🔍 Pylint gate: Checking staged Python files..."

# Check if pylint is available via uv
if ! uv run pylint --version &> /dev/null 2>&1; then
  echo "⚠️  pylint not available via uv. Skipping pylint gate."
  exit 0
fi

# Run pylint on staged files and capture the score
FULL_PATHS=""
for file in $STAGED_PY_FILES; do
  if [ -f "$GIT_ROOT/$file" ]; then
    FULL_PATHS="$FULL_PATHS $GIT_ROOT/$file"
  fi
done

if [ -z "$FULL_PATHS" ]; then
  exit 0
fi

PYLINT_OUTPUT=$(uv run pylint --score=y $FULL_PATHS 2>&1)
PYLINT_EXIT=$?

# Extract the score (format: "Your code has been rated at X.XX/10")
SCORE=$(echo "$PYLINT_OUTPUT" | grep -oE 'rated at [0-9]+\.[0-9]+' | grep -oE '[0-9]+\.[0-9]+')

if [ -z "$SCORE" ]; then
  echo "⚠️  Could not parse pylint score. Output:"
  echo "$PYLINT_OUTPUT" | tail -5
  exit 0
fi

# Compare score against threshold (8.0)
THRESHOLD="8.0"
PASSES=$(echo "$SCORE >= $THRESHOLD" | bc -l 2>/dev/null)

if [ "$PASSES" != "1" ]; then
  echo ""
  echo "❌ PYLINT SCORE TOO LOW — commit blocked"
  echo "───────────────────────────────────────────────────"
  echo "   Score: $SCORE/10 (minimum: $THRESHOLD/10)"
  echo ""
  echo "$PYLINT_OUTPUT" | grep -E '^(src/|[A-Z][0-9]{4}:)' | head -20
  echo ""
  echo "───────────────────────────────────────────────────"
  echo "💡 Fix issues and re-stage files."
  echo "   Run: uv run pylint src/budget_analyser/"
  echo ""
  echo "BLOCKING: Commit will not proceed until pylint score >= $THRESHOLD"
  exit 1
fi

echo "✅ Pylint score: $SCORE/10 (threshold: $THRESHOLD/10)"
exit 0
