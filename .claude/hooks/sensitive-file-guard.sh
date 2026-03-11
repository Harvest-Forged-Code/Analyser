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
  *.sqlite|*.db)
    SENSITIVE=true
    REASON="Database file — should not be committed"
    ;;
esac

# Check file content for sensitive patterns (if Write tool provides content)
CONTENT=$(echo "$INPUT" | grep -oE '"content"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"$//')

if [ -n "$CONTENT" ]; then
  # Check for API keys in TSX/TSX files
  case "$FILE_PATH" in
    *.tsx|*.ts|*.jsx|*.js)
      if echo "$CONTENT" | grep -qiE '(api[_-]?key|secret[_-]?key|auth[_-]?token)\s*[:=]\s*["\x27][A-Za-z0-9]'; then
        SENSITIVE=true
        REASON="Possible API key or secret token in frontend code"
      fi
      ;;
  esac

  # Check for hardcoded ports that differ from standard config
  if echo "$CONTENT" | grep -qE 'localhost:[0-9]{4,5}' 2>/dev/null; then
    case "$FILE_PATH" in
      *config*|*test*|*spec*|*playwright*|*CLAUDE*|*.md)
        # Skip config, test, and doc files — hardcoded ports are expected
        ;;
      *)
        echo "INFO: Hardcoded localhost port detected in $FILENAME — consider using config/env variable."
        ;;
    esac
  fi
fi

if [ "$SENSITIVE" = true ]; then
  echo "⚠️  SENSITIVE FILE WARNING: $REASON"
  echo "   File: $FILE_PATH"
  echo "   Ensure this file is in .gitignore and contains no hardcoded secrets."
fi

exit 0
