# ---
# name: security-audit
# description: >
#   Use when auditing code for security vulnerabilities, secrets exposure,
#   dependency issues, or compliance gaps. Produces a structured report with
#   findings categorized by severity and actionable remediation steps.
# trigger: >
#   When user asks for a security review, audit, vulnerability check, pen test
#   preparation, or compliance review.
#   Keywords: "security audit", "vulnerability", "security review", "secrets scan",
#   "dependency audit", "OWASP", "pen test prep", "hardening".
# inputs:
#   - scope: directories or files to audit (default: entire project)
#   - focus_areas: optional list of specific concerns (e.g., "auth", "SQL injection")
# references:
#   - CLAUDE.md [SECURITY] section
#   - OWASP Top 10 (2021): https://owasp.org/Top10/
#   - CWE Top 25: https://cwe.mitre.org/top25/
# ---

# Skill: security-audit

## Purpose

Perform a comprehensive security audit of the codebase, identifying vulnerabilities
across the OWASP Top 10 categories, secrets exposure, dependency risks, and
implementation flaws. The output is a structured report with severity ratings
and specific remediation guidance for every finding.

---

## OWASP Top 10 (2021) Reference

This audit checks for all categories. Keep these in mind throughout every step.

| #   | Category                                | Common Manifestations                       |
|-----|-----------------------------------------|---------------------------------------------|
| A01 | Broken Access Control                   | Missing auth checks, IDOR, privilege escalation |
| A02 | Cryptographic Failures                  | Weak hashing, plaintext secrets, bad TLS    |
| A03 | Injection                               | SQL injection, command injection, XSS       |
| A04 | Insecure Design                         | Missing threat model, no rate limiting      |
| A05 | Security Misconfiguration               | Debug mode in prod, default credentials     |
| A06 | Vulnerable and Outdated Components      | Unpatched deps, known CVEs                  |
| A07 | Identification and Authentication Failures | Weak passwords, broken session management |
| A08 | Software and Data Integrity Failures    | Unsigned updates, insecure deserialization  |
| A09 | Security Logging and Monitoring Failures | No audit logs, unmonitored errors          |
| A10 | Server-Side Request Forgery (SSRF)      | Unvalidated URLs in server requests         |

---

## Workflow

### Step 1 -- Scan for Hardcoded Secrets

Search the entire codebase for exposed credentials, API keys, tokens, and passwords.

**Search patterns:**
```bash
# API keys and tokens
grep -rn "api[_-]?key\s*=\s*['\"][^'\"]*['\"]" src/ --include="*.py"
grep -rn "token\s*=\s*['\"][^'\"]*['\"]" src/ --include="*.py"
grep -rn "secret\s*=\s*['\"][^'\"]*['\"]" src/ --include="*.py"

# Passwords
grep -rn "password\s*=\s*['\"][^'\"]*['\"]" src/ --include="*.py"
grep -rn "passwd\s*=\s*['\"]" src/ --include="*.py"

# Connection strings with embedded credentials
grep -rn "://[^:]+:[^@]+@" src/ --include="*.py"
grep -rn "DATABASE_URL\s*=\s*['\"]" src/ --include="*.py"

# AWS credentials
grep -rn "AKIA[0-9A-Z]{16}" src/
grep -rn "aws_secret_access_key" src/ --include="*.py"

# Private keys
grep -rn "BEGIN.*PRIVATE KEY" src/
grep -rn "BEGIN RSA" src/

# Generic high-entropy strings (potential secrets)
# Look for strings longer than 30 chars that look like keys/tokens
grep -rn "['\"][A-Za-z0-9+/=]{32,}['\"]" src/ --include="*.py"
```

**Check configuration files:**
- `.env` files committed to version control (should only be `.env.example`).
- `settings.py`, `config.py` for hardcoded values.
- `docker-compose.yml` for embedded passwords.
- CI/CD configs (`.github/workflows/`) for exposed secrets.
- Jupyter notebooks (`.ipynb`) for inline credentials.

**OWASP mapping:** A02 - Cryptographic Failures

**Severity:** CRITICAL if real credentials found; HIGH if patterns suggest likely exposure.

### Step 2 -- Check .gitignore for Sensitive File Patterns

Verify that `.gitignore` blocks all sensitive files from being committed.

**Required patterns:**
```
# Secrets and environment
.env
.env.*
!.env.example
*.pem
*.key
*.p12
*.pfx

# Credentials
credentials.json
service-account*.json
*secret*.json
*.keystore

# IDE and OS
.idea/
.vscode/settings.json
.DS_Store
Thumbs.db

# Python
__pycache__/
*.pyc
.venv/
venv/

# Data (if applicable)
*.csv
*.sqlite
*.db
data/raw/
```

**Verify no sensitive files are tracked:**
```bash
# Check if any .env files are tracked
git ls-files | grep -E "\.env$|\.env\." | grep -v ".example"

# Check for key/certificate files
git ls-files | grep -E "\.(pem|key|p12|pfx|keystore)$"

# Check for credential files
git ls-files | grep -E "(credentials|secret|service.account).*\.json$"

# Check git history for previously committed secrets
git log --all --diff-filter=A --name-only --pretty=format: | grep -E "\.(env|pem|key)$"
```

**OWASP mapping:** A02 - Cryptographic Failures, A05 - Security Misconfiguration

**Severity:** HIGH if sensitive files are tracked; MEDIUM if .gitignore is incomplete.

### Step 3 -- Review Input Validation on All External Boundaries

Identify every point where external data enters the application and verify validation.

**External boundaries to check:**
- HTTP request bodies (POST/PUT/PATCH payloads)
- URL path parameters
- Query string parameters
- HTTP headers (especially custom headers)
- File uploads
- WebSocket messages
- CLI arguments
- Environment variables
- Data read from external APIs
- Data read from message queues
- Data read from files (user-uploaded or external)

**For each boundary, verify:**
1. Input is validated before use (Pydantic models, explicit validation).
2. String inputs have maximum length constraints.
3. Numeric inputs have range constraints.
4. Enum inputs are validated against allowed values.
5. Email/URL inputs use proper validators.
6. File uploads check file type, size, and content (not just extension).
7. No raw user input is passed to system commands, SQL, or templates.

**Search for missing validation:**
```bash
# Direct request access without schema validation
grep -rn "request\.json\|request\.form\|request\.args\|request\.data" src/
grep -rn "request\.query_params\|request\.body()" src/

# Unvalidated path parameters
grep -rn "Path(\.\.\." src/ | grep -v "description"

# Raw string concatenation with user input
grep -rn "f\".*{.*request\|f\".*{.*param\|f\".*{.*query" src/
```

**OWASP mapping:** A03 - Injection (prevention), A04 - Insecure Design

**Severity:** HIGH for missing validation on security-critical inputs; MEDIUM for others.

### Step 4 -- Check for SQL Injection Vulnerabilities

Scan for unsafe database query construction.

**Dangerous patterns to find:**
```bash
# Raw SQL with string formatting
grep -rn "\.execute(f\"" src/ --include="*.py"
grep -rn "\.execute(\".*%s" src/ --include="*.py"
grep -rn "\.execute(\".*\" +" src/ --include="*.py"
grep -rn "\.execute(\".*\" \." src/ --include="*.py"
grep -rn "\.execute(\".*\.format(" src/ --include="*.py"

# Raw SQL in text() without bound parameters
grep -rn "text(f\"" src/ --include="*.py"
grep -rn "text(\".*\.format" src/ --include="*.py"

# String concatenation in WHERE clauses
grep -rn "WHERE.*\" \+" src/ --include="*.py"
grep -rn "WHERE.*f\"" src/ --include="*.py"

# Raw queries bypassing ORM
grep -rn "raw_connection\|raw_sql\|execute_raw" src/ --include="*.py"

# cursor.execute with string formatting
grep -rn "cursor\.execute(f\"" src/ --include="*.py"
```

**Safe patterns (confirm these are used instead):**
- SQLAlchemy ORM queries with `select()`, `where()`, `filter()`.
- Parameterized queries: `text("SELECT * FROM users WHERE id = :id")` with `.params(id=value)`.
- Pydantic-validated inputs passed to ORM methods.

**OWASP mapping:** A03 - Injection

**Severity:** CRITICAL for confirmed SQL injection vectors; HIGH for potential vectors.

### Step 5 -- Check for XSS Vulnerabilities

Scan for unsafe HTML/template rendering with unescaped user input.

**Dangerous patterns:**
```bash
# Jinja2 with autoescape disabled
grep -rn "autoescape\s*=\s*False" src/ --include="*.py"
grep -rn "Markup(" src/ --include="*.py"
grep -rn "|safe" src/ templates/ --include="*.html"
grep -rn "{% autoescape false %}" templates/ --include="*.html"

# Direct HTML construction with user input
grep -rn "f\"<.*{.*}.*>\"" src/ --include="*.py"
grep -rn "HTMLResponse(f\"" src/ --include="*.py"
grep -rn "\.format(.*user\|\.format(.*input\|\.format(.*param" src/ --include="*.py"

# innerHTML or document.write in JavaScript
grep -rn "innerHTML\s*=" src/ static/ templates/ --include="*.js" --include="*.html"
grep -rn "document\.write(" src/ static/ templates/ --include="*.js" --include="*.html"
grep -rn "v-html=" src/ templates/ --include="*.html" --include="*.vue"

# React dangerouslySetInnerHTML
grep -rn "dangerouslySetInnerHTML" src/ --include="*.jsx" --include="*.tsx"
```

**Verify for API-only projects:**
- Even APIs can have XSS if they return HTML content type.
- Check `Content-Type` headers on responses.
- Check for HTML in error messages returned to clients.

**OWASP mapping:** A03 - Injection (Cross-Site Scripting)

**Severity:** HIGH for confirmed XSS vectors; MEDIUM for potential vectors in API responses.

### Step 6 -- Review Authentication and Authorization Implementation

Audit the full auth flow for weaknesses.

**Authentication checks:**
```bash
# Find auth implementation
grep -rn "authenticate\|login\|sign_in\|verify_password" src/ --include="*.py"
grep -rn "JWT\|jwt\|JsonWebToken" src/ --include="*.py"
grep -rn "session\[.*user\|current_user" src/ --include="*.py"

# Password hashing
grep -rn "hashlib\|md5\|sha1\|sha256" src/ --include="*.py"  # Weak hashing
grep -rn "bcrypt\|argon2\|scrypt\|pbkdf2" src/ --include="*.py"  # Strong hashing

# Token configuration
grep -rn "expire\|expir\|ttl\|lifetime" src/ --include="*.py"
grep -rn "SECRET_KEY\|JWT_SECRET\|SIGNING_KEY" src/ --include="*.py"
```

**Verify:**
1. **Password storage**: Uses bcrypt, argon2, or scrypt (never MD5, SHA-1, SHA-256 alone).
2. **JWT tokens**: Have reasonable expiration (15-60 min for access, days for refresh).
3. **JWT signing**: Uses strong algorithm (RS256 or HS256 with strong secret, never `none`).
4. **Token refresh**: Refresh tokens are rotated on use and stored securely.
5. **Session management**: Sessions invalidated on logout and password change.
6. **Rate limiting**: Login endpoint has rate limiting to prevent brute force.
7. **Account lockout**: Account locks after N failed attempts.
8. **Password policy**: Minimum length (12+), complexity requirements.

**Authorization checks:**
```bash
# Find authorization patterns
grep -rn "permission\|role\|authorize\|is_admin\|is_superuser" src/ --include="*.py"
grep -rn "Depends(.*auth\|Depends(.*permission\|Depends(.*role" src/ --include="*.py"

# Find endpoints without auth dependencies
# Compare list of all endpoints vs endpoints with auth
grep -rn "@router\.\|@app\." src/ --include="*.py" | grep -v "Depends.*auth"
```

**Verify:**
1. All non-public endpoints require authentication.
2. Authorization checks are at the endpoint level (not just frontend).
3. Users cannot access other users' resources (IDOR check).
4. Admin functions are restricted to admin roles.
5. No privilege escalation paths (user cannot make themselves admin).

**OWASP mapping:** A01 - Broken Access Control, A07 - Identification and Authentication Failures

**Severity:** CRITICAL for missing auth on sensitive endpoints; HIGH for weak password hashing.

### Step 7 -- Run Dependency Audit

Check all project dependencies for known vulnerabilities.

**Run automated tools:**
```bash
# pip-audit (preferred)
pip-audit --requirement requirements.txt
# or
pip-audit --desc

# safety (alternative)
safety check --full-report

# If using poetry
poetry audit

# Check for outdated packages
pip list --outdated

# Check for packages with known issues
pip-audit --fix --dry-run
```

**Manual dependency review:**
- Check `pyproject.toml` or `requirements.txt` for pinned vs unpinned versions.
- Verify all dependencies are from trusted sources (PyPI, not arbitrary git repos).
- Check for typosquatting (package names that look like popular packages but differ by one character).
- Review any vendored or copied code for known vulnerabilities.

**Dependency hygiene rules:**
- All production dependencies must be pinned to exact versions or version ranges.
- Dev dependencies can use minimum version constraints.
- No `*` or unpinned versions in production dependencies.
- Review each dependency for maintenance status (last release date, open issues).

**OWASP mapping:** A06 - Vulnerable and Outdated Components

**Severity:** CRITICAL for deps with known exploits; HIGH for outdated deps with CVEs.

### Step 8 -- Check for Path Traversal in File Operations

Scan for unsafe file access that could allow path traversal attacks.

**Dangerous patterns:**
```bash
# File open with user-controlled paths
grep -rn "open(.*request\|open(.*param\|open(.*user" src/ --include="*.py"
grep -rn "open(f\"" src/ --include="*.py"

# Path construction with user input
grep -rn "os\.path\.join(.*request\|os\.path\.join(.*user" src/ --include="*.py"
grep -rn "Path(.*request\|Path(.*user\|Path(.*param" src/ --include="*.py"

# File operations
grep -rn "shutil\.\|os\.remove\|os\.unlink\|os\.rename" src/ --include="*.py"
grep -rn "send_file\|send_from_directory\|FileResponse" src/ --include="*.py"

# Subprocess with file paths
grep -rn "subprocess\.\|os\.system\|os\.popen" src/ --include="*.py"
```

**Verify for each file operation:**
1. User-supplied filenames are sanitized (strip `../`, null bytes).
2. File paths are resolved to absolute paths and validated against an allowed directory.
3. `os.path.realpath()` or `Path.resolve()` is used before access.
4. Directory listing endpoints restrict to intended directories.
5. File uploads save to a dedicated directory with generated filenames (not user-supplied).

**Safe pattern:**
```python
import os
from pathlib import Path

UPLOAD_DIR = Path("/app/uploads").resolve()

def safe_file_path(user_filename: str) -> Path:
    """Resolve and validate file path against allowed directory."""
    safe_name = Path(user_filename).name  # Strip directory components
    full_path = (UPLOAD_DIR / safe_name).resolve()
    if not str(full_path).startswith(str(UPLOAD_DIR)):
        raise ValueError("Path traversal attempt detected")
    return full_path
```

**OWASP mapping:** A01 - Broken Access Control, A03 - Injection

**Severity:** HIGH for confirmed path traversal; MEDIUM for potential vectors.

### Step 9 -- Review Error Handling

Ensure errors do not leak sensitive information to clients.

**Check for information leakage:**
```bash
# Stack traces in responses
grep -rn "traceback\|format_exc\|print_exc\|exc_info" src/ --include="*.py"
grep -rn "DEBUG\s*=\s*True" src/ --include="*.py"

# Verbose error messages
grep -rn "str(exc)\|str(e)\|repr(e)" src/ --include="*.py"

# Exception details in HTTP responses
grep -rn "detail=str(\|detail=repr(\|detail=.*exc" src/ --include="*.py"
grep -rn "HTTPException.*detail=.*Error" src/ --include="*.py"

# Database errors exposed
grep -rn "IntegrityError\|OperationalError\|ProgrammingError" src/ --include="*.py"
```

**Verify:**
1. Production config has `DEBUG=False`.
2. Global exception handler catches unhandled exceptions and returns generic error.
3. Stack traces are logged server-side but never returned to clients.
4. Database errors are caught and translated to user-friendly messages.
5. Validation errors show field-level errors but not internal implementation details.
6. 500 errors return a generic "Internal Server Error" message with a request ID.
7. Error responses follow the consistent error format (see api-design skill).

**Logging checks:**
```bash
# Sensitive data in logs
grep -rn "logger\.\|logging\.\|log\." src/ --include="*.py" | grep -i "password\|secret\|token\|key"
grep -rn "print(" src/ --include="*.py" | grep -i "password\|secret\|token"
```

**Verify:**
1. Passwords, tokens, and secrets are never logged.
2. PII is masked or omitted from logs.
3. Log levels are appropriate (no DEBUG in production).
4. Security-relevant events are logged (login, logout, failed auth, permission denied).

**OWASP mapping:** A09 - Security Logging and Monitoring Failures, A05 - Security Misconfiguration

**Severity:** HIGH for stack traces in production responses; MEDIUM for verbose errors.

### Step 10 -- Generate Security Audit Report

Compile all findings into a structured report.

**Report format:**

```markdown
# Security Audit Report

**Project:** {project_name}
**Date:** {date}
**Auditor:** Claude AI
**Scope:** {directories/files audited}

## Executive Summary

- Total findings: {count}
- Critical: {count}
- High: {count}
- Medium: {count}
- Low: {count}

## Findings

### [CRITICAL-001] {Title}

- **Severity:** CRITICAL
- **OWASP Category:** A03 - Injection
- **CWE:** CWE-89 (SQL Injection)
- **Location:** `src/project/api/routers/users.py:45`
- **Description:** Raw SQL query constructed with f-string using unvalidated user input.
- **Evidence:**
  ```python
  # Line 45
  query = f"SELECT * FROM users WHERE name = '{request.query_params['name']}'"
  ```
- **Impact:** An attacker can execute arbitrary SQL commands, potentially reading,
  modifying, or deleting all data in the database.
- **Remediation:**
  ```python
  # Use parameterized query
  stmt = select(User).where(User.name == name)
  result = await session.execute(stmt)
  ```
- **Verification:** After fix, run `ruff check` and confirm no f-string SQL patterns remain.

### [HIGH-001] {Title}
...

### [MEDIUM-001] {Title}
...

### [LOW-001] {Title}
...

## Dependency Audit Results

| Package       | Current | Vulnerable | CVE            | Severity | Fix Version |
|---------------|---------|------------|----------------|----------|-------------|
| package-name  | 1.2.3   | Yes        | CVE-2024-XXXXX | HIGH     | 1.2.4       |

## Recommendations Summary

### Immediate Actions (Critical/High)
1. {action with specific file and line reference}
2. {action with specific file and line reference}

### Short-term Actions (Medium)
1. {action}
2. {action}

### Long-term Improvements (Low / Hardening)
1. {action}
2. {action}

## OWASP Top 10 Coverage Matrix

| Category | Checked | Findings | Status |
|----------|---------|----------|--------|
| A01      | Yes     | 2        | FAIL   |
| A02      | Yes     | 0        | PASS   |
| A03      | Yes     | 1        | FAIL   |
| ...      | ...     | ...      | ...    |
```

**Report rules:**
- Every finding must have a specific file path and line number.
- Every finding must have a code example showing the vulnerability.
- Every finding must have a remediation code example.
- Severity ratings follow standard definitions:
  - **CRITICAL**: Exploitable with significant impact. Fix immediately.
  - **HIGH**: Exploitable or high impact. Fix within days.
  - **MEDIUM**: Potential risk or defense-in-depth gap. Fix within sprint.
  - **LOW**: Minor issue or hardening recommendation. Fix when convenient.
- Findings are ordered by severity (Critical first, then High, Medium, Low).
- Include the OWASP coverage matrix to show audit completeness.

---

## Enforced Standards

### Google-Style Docstrings (MANDATORY)
Every function, method, and class written or modified during the security audit MUST have a Google-style docstring. No exceptions. This includes:
- One-line summary in imperative mood
- Args section for all parameters
- Returns section describing what is returned
- Raises section for all exceptions
- See CLAUDE.md [STANDARDS] for full specification and examples.

### Git Commit Format (MANDATORY)
All commits created during the security audit MUST follow this format:
- **Signed commits**: Always use `git commit -S`
- **Semantic prefix**: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`, `ci:`
- **File-change table** in the commit body:
  ```
  type: concise description

  | File (Location) | Summary of Change |
  |---|---|
  | path/to/file.py | What changed in this file |

  Author: PrabhukumarSivamoorthy@gmail.com
  ```
- See CLAUDE.md [GIT] for full specification.

---

## Completion Checklist

- [ ] Scanned for hardcoded secrets (API keys, passwords, tokens, connection strings)
- [ ] Verified .gitignore covers all sensitive file patterns
- [ ] Confirmed no sensitive files are tracked in git history
- [ ] Reviewed input validation on all external boundaries
- [ ] Checked all database queries for SQL injection patterns
- [ ] Verified parameterized queries used throughout
- [ ] Scanned for XSS vulnerabilities in HTML/template rendering
- [ ] Verified autoescape enabled in template engines
- [ ] Reviewed password hashing (must be bcrypt/argon2/scrypt)
- [ ] Verified JWT token expiration and signing algorithm
- [ ] Confirmed all sensitive endpoints require authentication
- [ ] Checked for IDOR (users accessing other users' resources)
- [ ] Verified role-based authorization on admin endpoints
- [ ] Ran pip-audit or safety for dependency CVEs
- [ ] Verified all dependencies are pinned
- [ ] Checked for path traversal in file operations
- [ ] Verified file paths are resolved and validated against allowed directories
- [ ] Confirmed no stack traces leaked in production error responses
- [ ] Verified sensitive data not present in logs
- [ ] Confirmed security events are logged (auth, permissions)
- [ ] Generated structured report with all findings
- [ ] Every finding has file path, line number, evidence, and remediation
- [ ] OWASP Top 10 coverage matrix completed
- [ ] Report shared with user and remediation plan discussed
