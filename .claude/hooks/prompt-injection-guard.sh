#!/bin/bash
# Hook: prompt-injection-guard
# Event: PreToolUse (Write/Edit)
# Purpose: Scan for suspicious patterns that could indicate security issues

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')

if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$INPUT" | grep -oE '"path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"//')
fi

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

FILENAME=$(basename "$FILE_PATH")
EXT="${FILENAME##*.}"

# Only check code files
case "$EXT" in
  py|ts|tsx|js|jsx|sql|sh) ;;
  *) exit 0 ;;
esac

# Extract content to scan
# For Write: check "content" field
# For Edit: check "new_string" field
CONTENT=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    content = data.get('content', '') or data.get('new_string', '')
    print(content)
except:
    pass
" 2>/dev/null)

if [ -z "$CONTENT" ]; then
  exit 0
fi

WARNINGS=""

# Python-specific checks
case "$EXT" in
  py)
    # eval/exec with variables (potential code injection)
    if echo "$CONTENT" | grep -qE 'eval\s*\(\s*(f["\x27]|[a-zA-Z_])'; then
      WARNINGS="$WARNINGS\n  - eval() with dynamic input — potential code injection"
    fi
    if echo "$CONTENT" | grep -qE 'exec\s*\(\s*(f["\x27]|[a-zA-Z_])'; then
      WARNINGS="$WARNINGS\n  - exec() with dynamic input — potential code execution"
    fi

    # subprocess with shell=True and string formatting
    if echo "$CONTENT" | grep -qE 'subprocess\.(call|run|Popen).*shell\s*=\s*True' && echo "$CONTENT" | grep -qE '(f["\x27]|\.format\()'; then
      WARNINGS="$WARNINGS\n  - subprocess with shell=True and string formatting — command injection risk"
    fi

    # os.system with dynamic input
    if echo "$CONTENT" | grep -qE 'os\.system\s*\(\s*(f["\x27]|[a-zA-Z_])'; then
      WARNINGS="$WARNINGS\n  - os.system() with dynamic input — command injection risk"
    fi

    # SQL string concatenation
    if echo "$CONTENT" | grep -qE '(f["\x27]SELECT|f["\x27]INSERT|f["\x27]UPDATE|f["\x27]DELETE)'; then
      WARNINGS="$WARNINGS\n  - SQL query with f-string — SQL injection risk, use parameterized queries"
    fi
    if echo "$CONTENT" | grep -qE '"SELECT.*"\s*\+|"INSERT.*"\s*\+|"UPDATE.*"\s*\+|"DELETE.*"\s*\+'; then
      WARNINGS="$WARNINGS\n  - SQL query with string concatenation — SQL injection risk"
    fi

    # __import__ (dynamic import)
    if echo "$CONTENT" | grep -qE '__import__\s*\('; then
      WARNINGS="$WARNINGS\n  - __import__() — dynamic import, verify this is intentional"
    fi

    # pickle with untrusted data
    if echo "$CONTENT" | grep -qE 'pickle\.(loads|load)\s*\('; then
      WARNINGS="$WARNINGS\n  - pickle.loads() — deserializing untrusted data is a security risk"
    fi
    ;;
esac

# TypeScript/JavaScript-specific checks
case "$EXT" in
  ts|tsx|js|jsx)
    # dangerouslySetInnerHTML
    if echo "$CONTENT" | grep -qE 'dangerouslySetInnerHTML'; then
      WARNINGS="$WARNINGS\n  - dangerouslySetInnerHTML — XSS risk, sanitize HTML input"
    fi

    # innerHTML assignment
    if echo "$CONTENT" | grep -qE '\.innerHTML\s*='; then
      WARNINGS="$WARNINGS\n  - innerHTML assignment — XSS risk, use textContent or sanitized HTML"
    fi

    # eval()
    if echo "$CONTENT" | grep -qE '\beval\s*\('; then
      WARNINGS="$WARNINGS\n  - eval() — code injection risk"
    fi

    # new Function()
    if echo "$CONTENT" | grep -qE 'new\s+Function\s*\('; then
      WARNINGS="$WARNINGS\n  - new Function() — equivalent to eval, code injection risk"
    fi
    ;;
esac

# Shell-specific checks
case "$EXT" in
  sh)
    # eval with variables
    if echo "$CONTENT" | grep -qE 'eval\s.*\$'; then
      WARNINGS="$WARNINGS\n  - eval with variable expansion — command injection risk"
    fi
    ;;
esac

if [ -n "$WARNINGS" ]; then
  echo ""
  echo "🔒 Security patterns detected in $FILENAME:"
  echo -e "$WARNINGS"
  echo ""
  echo "   Review these patterns to ensure they are safe."
  echo "   The security-audit skill can perform a deeper analysis."
fi

# Always exit 0 — this is a warning, the security review hook handles blocking
exit 0
