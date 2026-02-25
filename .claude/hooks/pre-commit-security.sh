#!/bin/bash
# Hook: pre-commit-security
# Event: PreToolUse (Bash)
# Purpose: Block git commits until the financial-security-reviewer agent has reviewed
#          staged Python and TypeScript files. Checks for a clearance token written
#          by the agent. If the token is missing or stale, blocks the commit and
#          instructs Claude to invoke the financial-security-reviewer agent.

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

# Locate the project root
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$GIT_ROOT" ]; then
  exit 0
fi

# Check if any Python or TypeScript source files are staged
STAGED_CODE=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | \
  grep -E '\.(py|ts|tsx)$' | \
  grep -v '__pycache__\|\.d\.ts$' | \
  head -30)

if [ -z "$STAGED_CODE" ]; then
  # No code files staged — no security review needed
  exit 0
fi

# Compute hash of the current staged code files (order-independent)
STAGED_HASH=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | \
  grep -E '\.(py|ts|tsx)$' | \
  grep -v '__pycache__\|\.d\.ts$' | \
  sort | md5 -q 2>/dev/null || \
  git diff --cached --name-only --diff-filter=ACM 2>/dev/null | \
  grep -E '\.(py|ts|tsx)$' | \
  grep -v '__pycache__\|\.d\.ts$' | \
  sort | md5sum | awk '{print $1}')

CLEARANCE_FILE="$GIT_ROOT/.claude/.security-cleared"

# Check if a valid clearance token exists for this exact set of staged files
if [ -f "$CLEARANCE_FILE" ]; then
  STORED_HASH=$(cat "$CLEARANCE_FILE" | tr -d '[:space:]')
  if [ "$STORED_HASH" = "$STAGED_HASH" ]; then
    # Valid clearance — allow commit and clean up the token
    rm -f "$CLEARANCE_FILE"
    echo "✅ Security review clearance verified. Proceeding with commit."
    exit 0
  fi
fi

# No valid clearance — block commit and instruct Claude
echo ""
echo "🔐 SECURITY REVIEW REQUIRED — commit blocked"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Staged code files detected:"
echo "$STAGED_CODE" | sed 's/^/  • /'
echo ""
echo "INSTRUCTION: You must invoke the financial-security-reviewer agent"
echo "BEFORE this commit can proceed."
echo ""
echo "Steps:"
echo "  1. Invoke the 'financial-security-reviewer' agent to review the staged files above"
echo "  2. The agent uses the security-audit skill + financial data context"
echo "  3. If the review is clean, the agent will write the clearance token"
echo "  4. Then retry the git commit"
echo ""
echo "Staged hash: $STAGED_HASH"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "BLOCKING: Commit will not proceed until financial-security-reviewer clears it."

exit 1
