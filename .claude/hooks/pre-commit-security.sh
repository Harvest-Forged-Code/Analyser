#!/bin/bash
# Hook: pre-commit-security
# Event: PreToolUse (Bash | mcp__gitkraken__git_add_or_commit |
#                    mcp__github__push_files | mcp__github__create_or_update_file)
# Purpose: Block commits/pushes until financial-security-reviewer agent has cleared
#          staged/pushed Python and TypeScript files.
#
# Clearance flow:
#   Hook blocks → Claude invokes financial-security-reviewer agent →
#   Agent writes .claude/.security-cleared with file-list hash →
#   Hook finds valid token → commit proceeds (token deleted)

INPUT=$(cat)

# ---------------------------------------------------------------------------
# Detect which tool is calling and extract the relevant file list
# ---------------------------------------------------------------------------
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_name', ''))
" 2>/dev/null)

CODE_FILES=""
GIT_ROOT=""
USE_GIT_CACHE=false
SOURCE_LABEL=""

case "$TOOL_NAME" in

  # ── Bash: intercept `git commit` ─────────────────────────────────────────
  "Bash")
    COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('command', ''))
" 2>/dev/null)
    case "$COMMAND" in *"git commit"*) ;; *) exit 0 ;; esac
    GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
    [ -z "$GIT_ROOT" ] && exit 0
    USE_GIT_CACHE=true
    SOURCE_LABEL="Bash"
    ;;

  # ── GitKraken MCP: intercept action=commit ───────────────────────────────
  "mcp__gitkraken__git_add_or_commit")
    ACTION=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('action', ''))
" 2>/dev/null)
    [ "$ACTION" != "commit" ] && exit 0
    DIRECTORY=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('directory', ''))
" 2>/dev/null)
    GIT_ROOT=$(cd "$DIRECTORY" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null)
    [ -z "$GIT_ROOT" ] && exit 0
    USE_GIT_CACHE=true
    SOURCE_LABEL="GitKraken MCP"
    ;;

  # ── GitHub MCP push_files: extract paths from files[] array ──────────────
  "mcp__github__push_files")
    CODE_FILES=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
files = d.get('tool_input', {}).get('files', [])
code = [
  f['path'] for f in files
  if isinstance(f, dict)
  and 'path' in f
  and any(f['path'].endswith(ext) for ext in ('.py', '.ts', '.tsx'))
  and '__pycache__' not in f['path']
  and not f['path'].endswith('.d.ts')
]
print('\n'.join(sorted(code)))
" 2>/dev/null)
    GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
    [ -z "$GIT_ROOT" ] && GIT_ROOT="."
    USE_GIT_CACHE=false
    SOURCE_LABEL="GitHub MCP (push_files)"
    ;;

  # ── GitHub MCP create_or_update_file: single file path ───────────────────
  "mcp__github__create_or_update_file")
    FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('path', ''))
" 2>/dev/null)
    if echo "$FILE_PATH" | grep -qE '\.(py|ts|tsx)$' && \
       ! echo "$FILE_PATH" | grep -q '__pycache__\|\.d\.ts'; then
      CODE_FILES="$FILE_PATH"
    fi
    GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
    [ -z "$GIT_ROOT" ] && GIT_ROOT="."
    USE_GIT_CACHE=false
    SOURCE_LABEL="GitHub MCP (create_or_update_file)"
    ;;

  *)
    exit 0
    ;;
esac

# ---------------------------------------------------------------------------
# For local-git tools (Bash, GitKraken), derive file list from staging area
# ---------------------------------------------------------------------------
if [ "$USE_GIT_CACHE" = "true" ]; then
  CODE_FILES=$(git -C "$GIT_ROOT" diff --cached --name-only --diff-filter=ACM 2>/dev/null | \
    grep -E '\.(py|ts|tsx)$' | \
    grep -v '__pycache__\|\.d\.ts$' | \
    head -30)
fi

# Nothing to review
[ -z "$CODE_FILES" ] && exit 0

# ---------------------------------------------------------------------------
# Compute hash from sorted file list (same logic the agent uses to clear)
# ---------------------------------------------------------------------------
STAGED_HASH=$(echo "$CODE_FILES" | sort | md5 -q 2>/dev/null || \
              echo "$CODE_FILES" | sort | md5sum | awk '{print $1}')

CLEARANCE_FILE="$GIT_ROOT/.claude/.security-cleared"

# ---------------------------------------------------------------------------
# Check for valid clearance token
# ---------------------------------------------------------------------------
if [ -f "$CLEARANCE_FILE" ]; then
  STORED_HASH=$(tr -d '[:space:]' < "$CLEARANCE_FILE")
  if [ "$STORED_HASH" = "$STAGED_HASH" ]; then
    rm -f "$CLEARANCE_FILE"
    echo "✅ Security review clearance verified. Proceeding with commit. [$SOURCE_LABEL]"
    exit 0
  fi
fi

# ---------------------------------------------------------------------------
# Block and instruct Claude to invoke the financial-security-reviewer agent
# ---------------------------------------------------------------------------
echo ""
echo "🔐 SECURITY REVIEW REQUIRED — commit blocked [$SOURCE_LABEL]"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Code files detected:"
echo "$CODE_FILES" | sed 's/^/  • /'
echo ""
echo "INSTRUCTION: Invoke the 'financial-security-reviewer' agent before retrying."
echo ""
if [ "$USE_GIT_CACHE" = "false" ]; then
  echo "NOTE: This is a GitHub MCP push (bypasses local git staging)."
  echo "The agent must review the files listed above by reading them from disk."
  echo "The agent must compute the clearance hash from this exact file list:"
  echo "  echo \"$CODE_FILES\" | sort | md5sum | awk '{print \$1}'"
  echo ""
fi
echo "Expected clearance hash: $STAGED_HASH"
echo "Clearance file:          $CLEARANCE_FILE"
echo "═══════════════════════════════════════════════════════════════"
echo "BLOCKING: Commit will not proceed until financial-security-reviewer clears it."

exit 1
