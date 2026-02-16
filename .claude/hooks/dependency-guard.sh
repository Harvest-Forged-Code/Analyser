#!/bin/bash
# Hook: dependency-guard
# Event: PreToolUse (Bash)
# Purpose: Warn before installing dependencies from unknown sources

# Read the tool input from stdin
INPUT=$(cat)

# Extract the command
COMMAND=$(echo "$INPUT" | grep -oE '"command"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Check for package installation commands
INSTALLING=false
REASON=""

case "$COMMAND" in
  *"pip install"*|*"pip3 install"*|*"uv pip install"*|*"uv add"*)
    INSTALLING=true
    REASON="Python package installation detected"
    ;;
  *"npm install"*|*"npm i "*|*"yarn add"*|*"pnpm add"*)
    INSTALLING=true
    REASON="Node.js package installation detected"
    ;;
  *"brew install"*)
    INSTALLING=true
    REASON="Homebrew package installation detected"
    ;;
  *"curl"*"|"*"sh"*|*"curl"*"|"*"bash"*)
    INSTALLING=true
    REASON="⚠️  Piping remote script to shell detected — HIGH RISK"
    ;;
  *"wget"*"&&"*"sh"*|*"wget"*"&&"*"bash"*)
    INSTALLING=true
    REASON="⚠️  Downloading and executing remote script — HIGH RISK"
    ;;
esac

if [ "$INSTALLING" = true ]; then
  echo "📦 Dependency Guard: $REASON"
  echo "   Command: $COMMAND"
  echo "   Reminder: Pin versions, check package reputation, run 'pip-audit' after install."
fi

exit 0
