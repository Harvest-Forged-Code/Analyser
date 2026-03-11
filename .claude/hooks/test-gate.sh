#!/bin/bash
# Hook: test-gate
# Event: PreToolUse (Bash)
# Purpose: Block commits unless unit tests pass

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

# Check if there are staged Python source files (not just docs/configs)
STAGED_SRC_FILES=$(git diff --cached --name-only --diff-filter=ACM -- 'src/budget_analyser/**/*.py' 'src/test/**/*.py' 2>/dev/null)

if [ -z "$STAGED_SRC_FILES" ]; then
  exit 0
fi

echo "🧪 Test gate: Running unit tests..."

if ! uv run pytest --version &> /dev/null 2>&1; then
  echo "⚠️  pytest not available via uv. Skipping test gate."
  exit 0
fi

TEST_OUTPUT=$(cd "$GIT_ROOT" && uv run pytest src/test/unit/ -q --tb=short 2>&1)
TEST_EXIT=$?

if [ $TEST_EXIT -ne 0 ]; then
  # Count failures
  FAILED=$(echo "$TEST_OUTPUT" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' | head -1)
  PASSED=$(echo "$TEST_OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1)

  echo ""
  echo "❌ UNIT TESTS FAILED — commit blocked"
  echo "───────────────────────────────────────────────────"
  echo "   Failed: ${FAILED:-?}  |  Passed: ${PASSED:-?}"
  echo ""
  echo "$TEST_OUTPUT" | grep -E '(FAILED|ERROR|assert)' | head -15
  echo ""
  echo "───────────────────────────────────────────────────"
  echo "💡 Fix failing tests: uv run pytest src/test/unit/ -v"
  echo ""
  echo "BLOCKING: Commit will not proceed until all unit tests pass."
  exit 1
fi

PASSED=$(echo "$TEST_OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1)
echo "✅ All unit tests passed (${PASSED:-0} tests)."
exit 0
