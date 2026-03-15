---
name: git-commit
description: Use when creating git commits — enforces signed commits, semantic format, and file-change table in commit messages
trigger: When committing code, preparing commits, or when any agent needs to commit changes
type: rigid
reference: CLAUDE.md [GIT]
---

# Git Commit Skill

## Purpose
Ensure every git commit follows the project's mandatory format: **signed**, **semantic prefix**, **file-change table**, and **Author trailer**.

---

## Setup (One-Time)

Configure GPG signing for all commits:

```bash
# Generate GPG key (if you don't have one)
gpg --full-generate-key

# Get your key ID
gpg --list-secret-keys --keyid-format=long

# Configure git to sign all commits
git config --global commit.gpgsign true
git config --global user.signingkey YOUR_KEY_ID

# For GitHub: export and add your public key
gpg --armor --export YOUR_KEY_ID
# Paste at: GitHub → Settings → SSH and GPG keys → New GPG key
```

---

## Commit Message Format

Every commit MUST follow this exact structure:

```
type: concise description in imperative mood

| File (Location) -| Summary of Change                      |
|------------------|----------------------------------------|
| path/to/file1.py | What specifically changed in this file |
| path/to/file2.py | What specifically changed in this file |

Author: PrabhukumarSivamoorthy@gmail.com
```

### Structure Rules

1. **First line** — `type: description`
   - Max 72 characters total
   - Imperative mood ("add", "fix", "refactor" — not "added", "fixes", "refactoring")
   - No period at the end
   - Lowercase after the colon

2. **Blank line** — Always separate the header from the body

3. **File-change table** — Every file modified gets a row
   - `File (Location)`: Relative path from project root
   - `Summary of Change`: Specific description of what changed (not just "updated" or "modified")
   - Table header and separator are mandatory

4. **Blank line** — Separate table from trailer

5. **Author trailer** — Always include when Claude assisted

---

## Semantic Commit Types

| Type | When to Use | Example |
|------|-------------|---------|
| `feat` | New feature or functionality | `feat: add user registration endpoint` |
| `fix` | Bug fix | `fix: correct discount calculation for zero-quantity items` |
| `refactor` | Code restructuring, no behavior change | `refactor: extract payment logic into PaymentService class` |
| `test` | Adding or updating tests only | `test: add integration tests for order cancellation flow` |
| `docs` | Documentation changes only | `docs: update API reference for v2 authentication endpoints` |
| `chore` | Dependencies, config, tooling | `chore: upgrade FastAPI to 0.115.0` |
| `ci` | CI/CD pipeline changes | `ci: add pip-audit security scanning to GitHub Actions` |
| `perf` | Performance improvements | `perf: add Redis caching to user profile lookups` |
| `security` | Security fixes or hardening | `security: add rate limiting to authentication endpoints` |

### Choosing the Right Type
- If it adds something users can see/use → `feat`
- If it fixes broken behavior → `fix`
- If it changes structure but not behavior → `refactor`
- If it only touches test files → `test`
- If it only touches docs/README/comments → `docs`
- If it changes CI/CD configs → `ci`
- If it makes things faster without behavior change → `perf`
- If it fixes a vulnerability or adds security controls → `security`
- Everything else (deps, tooling, config) → `chore`

---

## Examples

### Single-File Bug Fix
```
fix: prevent division by zero in discount calculation

| File (Location) | Summary of Change |
|---|---|
| src/orders/service.py | Added zero-quantity guard in calculate_discount() |

Author: PrabhukumarSivamoorthy@gmail.com
```

### Multi-File Feature
```
feat: add user registration with email verification

| File (Location) | Summary of Change |
|---|---|
| src/users/routes.py | Added POST /api/v1/users endpoint with request validation |
| src/users/service.py | Created UserService.register() with email uniqueness check |
| src/users/models.py | Added User model with email, hashed_password, is_verified fields |
| src/users/repository.py | Added UserRepository with save() and find_by_email() methods |
| src/users/schemas.py | Created UserCreateRequest and UserResponse Pydantic models |
| src/email/service.py | Added send_verification_email() with template rendering |
| tests/unit/test_user_service.py | Added 12 tests covering registration happy path and edge cases |
| tests/integration/test_user_api.py | Added 6 API integration tests for registration endpoint |

Author: PrabhukumarSivamoorthy@gmail.com
```

### Refactoring
```
refactor: extract payment processing into dedicated service

| File (Location) | Summary of Change |
|---|---|
| src/payments/service.py | Created PaymentService with process() and refund() methods |
| src/payments/processors.py | Extracted StripeProcessor and PayPalProcessor from OrderService |
| src/orders/service.py | Replaced inline payment logic with PaymentService dependency |
| src/orders/routes.py | Updated dependency injection to include PaymentService |
| tests/unit/test_payment_service.py | Added 15 unit tests for PaymentService |
| tests/unit/test_order_service.py | Updated 8 tests to use mocked PaymentService |

Author: PrabhukumarSivamoorthy@gmail.com
```

### CI/CD Change
```
ci: add security scanning and coverage reporting to CI pipeline

| File (Location) | Summary of Change |
|---|---|
| .github/workflows/ci.yml | Added pip-audit step, bandit SAST scan, coverage upload to Codecov |
| pyproject.toml | Added bandit and pip-audit to dev dependencies |
| Makefile | Added 'make security' target for local security scanning |

Author: PrabhukumarSivamoorthy@gmail.com
```

### Test-Only Commit
```
test: add edge case tests for order total calculation

| File (Location) | Summary of Change |
|---|---|
| tests/unit/test_order_service.py | Added 6 tests: empty cart, single item, max quantity, negative price guard, float precision, bulk discount threshold |
| tests/factories.py | Added OrderItemFactory with configurable price and quantity traits |

Author: PrabhukumarSivamoorthy@gmail.com
```

### Documentation-Only Commit
```
docs: update README with local development setup instructions

| File (Location) | Summary of Change |
|---|---|
| README.md | Added Prerequisites, Installation, Running Locally, and Running Tests sections |
| docs/architecture.md | Created architecture overview with Mermaid component diagram |

Author: PrabhukumarSivamoorthy@gmail.com
```

---

## Workflow — Use GitKraken MCP Tools

All git operations MUST use the GitKraken MCP tools. They produce structured, token-efficient output.

### Step 1: Check status

```
mcp__gitkraken__git_status(directory: ".")
```

Review untracked and modified files. Identify which files to stage.

### Step 2: Review recent commits (for style reference)

```
mcp__gitkraken__git_log_or_diff(directory: ".", action: "log")
```

### Step 3: Review changes

```
mcp__gitkraken__git_log_or_diff(directory: ".", action: "diff")
```

Confirm the diff matches intent. Check for secrets or `.env` files.

### Step 4: Stage specific files

```
mcp__gitkraken__git_add_or_commit(
  directory: ".",
  action: "add",
  files: ["path/to/file1.py", "path/to/file2.py"]
)
```

**Never stage all files blindly.** List each file explicitly.

### Step 5: Compose and commit

```
mcp__gitkraken__git_add_or_commit(
  directory: ".",
  action: "commit",
  message: "type: concise description\n\n| File (Location) | Summary of Change |\n|---|---|\n| path/to/file.py | What changed |\n\nAuthor: PrabhukumarSivamoorthy@gmail.com"
)
```

### Step 6: Verify

```
mcp__gitkraken__git_log_or_diff(directory: ".", action: "log")
```

Confirm the commit appears with the correct message format.

### Step 7: Push (only if requested)

```
mcp__gitkraken__git_push(directory: ".")
```

---

## Common Mistakes to Avoid

| Mistake | Why It's Wrong | Correct Approach |
|---------|---------------|-----------------|
| `Updated files` | Too vague — says nothing about what changed | Describe the specific change per file |
| Missing table rows | Some files not listed — incomplete record | Every staged file gets a row |
| `feat: Added login` | Past tense — should be imperative | `feat: add login endpoint` |
| Summary says "modified" | Doesn't explain what was modified | Describe the actual modification |
| No blank line after header | Breaks git formatting conventions | Always blank line between header and body |
| Table without header row | Invalid markdown table | Always include `| File (Location) | Summary of Change |` and `|---|---|` |
| Line > 72 chars in header | Breaks git log formatting | Keep first line under 72 characters |

---

## Pre-Commit Verification

Before committing, verify:
- [ ] All staged files are intentional (reviewed via `git_log_or_diff` diff)
- [ ] No secrets or `.env` files in the staged changes
- [ ] All functions have Google-style docstrings
- [ ] Tests pass (`uv run pytest src/test/unit/ -q`)
- [ ] Lint passes (`uv run pylint src/budget_analyser`)
- [ ] Commit message follows the format above
