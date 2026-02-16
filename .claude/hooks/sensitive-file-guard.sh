#!/bin/bash
# Hook: sensitive-file-guard
# Event: PreToolUse (Write/Edit)
# Purpose: Warn before writing to sensitive files (.env, secrets, config files with credentials)

# Read the tool input from stdin
INPUT=$(cat)

# Extract the file path from the tool input
FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')

if [ -z "$FILE_PATH" ]; then
  # Try alternate key names
  FILE_PATH=$(echo "$INPUT" | grep -oE '"path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')
fi

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Get the filename
FILENAME=$(basename "$FILE_PATH")

# Check against sensitive file patterns
SENSITIVE=false
REASON=""

case "$FILENAME" in
  .env|.env.*|*.env)
    SENSITIVE=true
    REASON="Environment file may contain secrets"
    ;;
  *secret*|*credential*|*password*)
    SENSITIVE=true
    REASON="Filename suggests sensitive content"
    ;;
  *key*.json|*key*.yml|*key*.yaml)
    SENSITIVE=true
    REASON="Filename suggests API keys or credentials"
    ;;
  *.pem|*.key|*.p12|*.pfx|*.jks)
    SENSITIVE=true
    REASON="Certificate or private key file"
    ;;
  id_rsa|id_ed25519|id_ecdsa)
    SENSITIVE=true
    REASON="SSH private key"
    ;;
esac

# Also check path patterns
case "$FILE_PATH" in
  */secrets/*|*/.secrets/*)
    SENSITIVE=true
    REASON="File is in a secrets directory"
    ;;
  */credentials/*|*/.credentials/*)
    SENSITIVE=true
    REASON="File is in a credentials directory"
    ;;
esac

if [ "$SENSITIVE" = true ]; then
  echo "⚠️  SENSITIVE FILE WARNING: $REASON"
  echo "   File: $FILE_PATH"
  echo "   Ensure this file is in .gitignore and contains no hardcoded secrets."
fi

exit 0
