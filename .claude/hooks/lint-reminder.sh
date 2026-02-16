#!/bin/bash
# Hook: lint-reminder
# Event: PostToolUse (Write/Edit)
# Purpose: Remind to run linting/formatting after code changes

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

# Get the file extension
EXT="${FILE_PATH##*.}"

# Only remind for source code files
case "$EXT" in
  py)
    echo "💡 Lint reminder: Run 'ruff check --fix $FILE_PATH && ruff format $FILE_PATH'"
    ;;
  ts|tsx|js|jsx)
    echo "💡 Lint reminder: Run 'eslint --fix $FILE_PATH && prettier --write $FILE_PATH'"
    ;;
  yaml|yml)
    echo "💡 Lint reminder: Run 'yamllint $FILE_PATH'"
    ;;
esac

exit 0
