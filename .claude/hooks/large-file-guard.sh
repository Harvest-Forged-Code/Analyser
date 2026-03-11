#!/bin/bash
# Hook: large-file-guard
# Event: PreToolUse (Write)
# Purpose: Warn/block when writing files that are too large

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

FILENAME=$(basename "$FILE_PATH")
EXT="${FILENAME##*.}"

# Skip non-code files (binary, images, data)
case "$EXT" in
  png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot|pdf|zip|tar|gz|db|sqlite)
    exit 0
    ;;
esac

# Skip lock files and generated files
case "$FILENAME" in
  package-lock.json|uv.lock|yarn.lock|Cargo.lock|*.min.js|*.min.css)
    exit 0
    ;;
esac

# Extract the content to check its size
# For Write tool, content is in the "content" field
CONTENT=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    content = data.get('content', '')
    print(content)
except:
    pass
" 2>/dev/null)

if [ -z "$CONTENT" ]; then
  exit 0
fi

# Count lines
LINE_COUNT=$(echo "$CONTENT" | wc -l | tr -d ' ')

# Count bytes
BYTE_COUNT=$(echo "$CONTENT" | wc -c | tr -d ' ')

# Hard block at 50KB
if [ "$BYTE_COUNT" -gt 50000 ] 2>/dev/null; then
  echo ""
  echo "❌ LARGE FILE BLOCKED: $FILENAME"
  echo "───────────────────────────────────────────────────"
  echo "   Size: ${BYTE_COUNT} bytes ($LINE_COUNT lines)"
  echo "   Limit: 50,000 bytes"
  echo ""
  echo "💡 Consider splitting this file into smaller modules."
  echo "   Large files are harder to maintain and review."
  echo ""
  echo "BLOCKING: File exceeds 50KB size limit."
  exit 1
fi

# Warning at 500 lines
if [ "$LINE_COUNT" -gt 500 ] 2>/dev/null; then
  echo ""
  echo "⚠️  LARGE FILE WARNING: $FILENAME"
  echo "   Lines: $LINE_COUNT (recommended max: 500)"
  echo "   Consider splitting into smaller, focused modules."
fi

exit 0
