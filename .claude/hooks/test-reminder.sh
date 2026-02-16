#!/bin/bash
# Hook: test-reminder
# Event: PostToolUse (Write/Edit)
# Purpose: Remind to run tests after modifying source code files

# Read the tool input from stdin
INPUT=$(cat)

# Extract the file path
FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')

if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$INPUT" | grep -oE '"path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')
fi

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Only remind for source code files (not test files, configs, docs)
FILENAME=$(basename "$FILE_PATH")
EXT="${FILE_PATH##*.}"

# Skip non-source files
case "$EXT" in
  py|ts|tsx|js|jsx) ;; # Continue for source files
  *) exit 0 ;;          # Skip everything else
esac

# Skip test files themselves
case "$FILENAME" in
  test_*|*_test.*|*.test.*|*spec.*|conftest.py)
    exit 0
    ;;
esac

# Skip config and non-logic files
case "$FILENAME" in
  __init__.py|setup.py|conftest.py|*.config.*|*.conf.*)
    exit 0
    ;;
esac

# Check if file is in a source directory (not tests, docs, scripts)
case "$FILE_PATH" in
  */tests/*|*/test/*|*/docs/*|*/scripts/*|*/migrations/*)
    exit 0
    ;;
esac

echo "🧪 Test reminder: Source file modified. Run 'pytest' to verify no regressions."

# Try to suggest a specific test file
DIR=$(dirname "$FILE_PATH")
MODULE=$(basename "$FILE_PATH" ."$EXT")

# Look for matching test file
for TEST_DIR in "tests" "test" "../tests" "tests/unit" "tests/integration"; do
  if [ -f "$DIR/$TEST_DIR/test_$MODULE.$EXT" ]; then
    echo "   Suggested: pytest $DIR/$TEST_DIR/test_$MODULE.$EXT"
    break
  fi
done

exit 0
