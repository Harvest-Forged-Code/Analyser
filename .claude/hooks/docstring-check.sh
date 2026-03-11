#!/bin/bash
# Hook: docstring-check
# Event: PostToolUse (Write/Edit)
# Purpose: Warn when new/modified public functions lack Google-style docstrings

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')

if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$INPUT" | grep -oE '"path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')
fi

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Only check Python files
case "$FILE_PATH" in
  *.py) ;;
  *) exit 0 ;;
esac

FILENAME=$(basename "$FILE_PATH")

# Skip test files, init files, conftest
case "$FILENAME" in
  test_*|*_test.py|conftest.py|__init__.py|setup.py)
    exit 0
    ;;
esac

# Skip non-source directories
case "$FILE_PATH" in
  */test/*|*/tests/*|*/migrations/*|*/scripts/*)
    exit 0
    ;;
esac

if [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

# Find public functions/methods without docstrings
# Look for lines with "def " that are NOT followed by a docstring on the next non-blank line
MISSING_DOCSTRINGS=$(awk '
  /^[[:space:]]*(def )[a-zA-Z]/ && !/^[[:space:]]*def _/ {
    func_line = NR
    func_name = $0
    gsub(/^[[:space:]]*def /, "", func_name)
    gsub(/\(.*/, "", func_name)
    getline
    # Skip blank lines
    while (/^[[:space:]]*$/) { getline }
    # Check if next non-blank line is a docstring
    if (!/"""/ && !/'\'''\'''\''/) {
      printf "  Line %d: %s()\n", func_line, func_name
    }
  }
' "$FILE_PATH" 2>/dev/null)

if [ -n "$MISSING_DOCSTRINGS" ]; then
  COUNT=$(echo "$MISSING_DOCSTRINGS" | wc -l | tr -d ' ')
  echo "📝 Docstring reminder: $COUNT public function(s) in $FILENAME missing Google-style docstrings:"
  echo "$MISSING_DOCSTRINGS"
  echo "   Style: \"\"\"Brief summary.\\n\\n    Args:\\n        param: Description.\\n\\n    Returns:\\n        Description.\\n    \"\"\""
fi

# Always exit 0 — this is a warning, never a blocker
exit 0
