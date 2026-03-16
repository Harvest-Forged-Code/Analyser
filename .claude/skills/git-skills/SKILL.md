---
name: git-skills
description: Use when performing any git operation — commits, branching, pushing, stashing, or viewing history. Enforces signed commits, semantic format with scope, and file-change table in commit messages.
trigger: When committing code, preparing commits, branching, pushing, or when any agent needs to perform git operations
type: rigid
reference: CLAUDE.md [GIT]
---

# Git Skills

## Purpose
Standardize all git operations — commits, branching, pushing, and history — using GitKraken MCP tools and the project's mandatory commit format: **signed**, **semantic prefix with scope**, **file-change table**, and **Author trailer**.

---

## Commit Message Format

Every commit MUST follow this exact structure:

```
<type>(<scope>): <short description>

| Area       | Change                              |
|------------|-------------------------------------|
| models.py  | Added Account frozen dataclass      |
| service.py | Added calculate_net_worth_summary() |

Author: Prabhukumar Sivamorthy
```

### Structure Rules

1. **First line** — `type(scope): description`
   - `<type>` — commit category (see Semantic Commit Types below)
   - `<scope>` — affected feature or module (e.g. `budget_goals`, `net_worth`, `api`, `ingestion`)
   - `<short description>` — imperative, lowercase, no period, max 72 characters total
   - Imperative mood ("add", "fix", "refactor" — not "added", "fixes", "refactoring")

2. **Blank line** — Always separate the header from the body

3. **File-change table** — A markdown table listing each changed area and what changed
   - Column 1: `Area` — file name or path relative to the feature (e.g. `models.py`, `api/routers/`, `test_*.py`)
   - Column 2: `Change` — specific description of what changed (not just "updated" or "modified")
   - Table header and separator are mandatory
   - Every staged file gets a row

4. **Blank line** — Separate table from trailer

5. **Author trailer** — `Author: Prabhukumar Sivamorthy`

---

## Semantic Commit Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Code style (formatting, no logic change) |
| `refactor` | Code refactoring (no feature/fix) |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks, dependencies |

### Choosing the Right Type
- If it adds something users can see/use → `feat`
- If it fixes broken behavior → `fix`
- If it only touches docs/README/comments → `docs`
- If it changes formatting with no logic change → `style`
- If it changes structure but not behavior → `refactor`
- If it only touches test files → `test`
- Everything else (deps, tooling, config, CI) → `chore`

---

## Examples

### Feature with Scope
```
feat(net_worth): add account balance history tracking

| Area             | Change                                   |
|------------------|------------------------------------------|
| models.py        | Added BalanceSnapshot frozen dataclass   |
| repository.py    | Added save_snapshot() and get_history()  |
| service.py       | Added compute_balance_trend() function   |
| api/routers/     | Added GET /net-worth/history endpoint    |

Author: Prabhukumar Sivamorthy
```

### Bug Fix with Scope
```
fix(ingestion): handle empty CSV files without crashing

| Area         | Change                                        |
|--------------|-----------------------------------------------|
| service.py   | Added early return guard for empty DataFrame  |
| test_*.py    | Added regression test for empty file input    |

Author: Prabhukumar Sivamorthy
```

### Refactoring
```
refactor(payments): extract payment processing into dedicated service

| Area                          | Change                                                |
|-------------------------------|-------------------------------------------------------|
| payments/service.py           | Created PaymentService with process() and refund()    |
| payments/processors.py        | Extracted StripeProcessor and PayPalProcessor          |
| orders/service.py             | Replaced inline payment logic with PaymentService     |
| test_payment_service.py       | Added 15 unit tests for PaymentService                |
| test_order_service.py         | Updated 8 tests to use mocked PaymentService          |

Author: Prabhukumar Sivamorthy
```

### Test-Only Commit
```
test(budget_goals): add edge case tests for budget limit calculation

| Area                          | Change                                                         |
|-------------------------------|----------------------------------------------------------------|
| test_budget_goals_service.py  | Added 6 tests: zero budget, negative amounts, float precision  |
| conftest.py                   | Added budget_goal_factory fixture                              |

Author: Prabhukumar Sivamorthy
```

### Chore (Dependencies, CI, Config)
```
chore(deps): upgrade FastAPI to 0.115.0

| Area              | Change                                        |
|-------------------|-----------------------------------------------|
| pyproject.toml    | Bumped fastapi from 0.114.2 to 0.115.0        |
| uv.lock           | Regenerated lock file                         |

Author: Prabhukumar Sivamorthy
```

### Documentation-Only Commit
```
docs(readme): update README with local development setup

| Area               | Change                                                        |
|--------------------|---------------------------------------------------------------|
| README.md          | Added Prerequisites, Installation, and Running Tests sections |
| docs/architecture.md | Created architecture overview with Mermaid diagram          |

Author: Prabhukumar Sivamorthy
```

---

## Workflow — Use GitKraken MCP Tools

All git operations MUST use the GitKraken MCP tools. They produce structured, token-efficient output.

### Step 1: Sync with remote main

Before any commit or push, always rebase onto the latest `origin/main` to avoid conflicts and keep history clean.

```bash
git fetch origin && git rebase origin/main
```

If rebase conflicts occur, resolve them before proceeding. After rebasing, use `git push --force-with-lease` (never `--force`) to update the remote branch.

### Step 2: Check status

```
mcp__gitkraken__git_status(directory: ".")
```

Review untracked and modified files. Identify which files to stage.

### Step 3: Review recent commits (for style reference)

```
mcp__gitkraken__git_log_or_diff(directory: ".", action: "log")
```

### Step 4: Review changes

```
mcp__gitkraken__git_log_or_diff(directory: ".", action: "diff")
```

Confirm the diff matches intent. Check for secrets or `.env` files.

### Step 5: Stage specific files

```
mcp__gitkraken__git_add_or_commit(
  directory: ".",
  action: "add",
  files: ["path/to/file1.py", "path/to/file2.py"]
)
```

**Never stage all files blindly.** List each file explicitly.

### Step 6: Compose and commit

```
mcp__gitkraken__git_add_or_commit(
  directory: ".",
  action: "commit",
  message: "type(scope): concise description\n\n| Area | Change |\n|---|---|\n| file.py | What changed |\n\nAuthor: Prabhukumar Sivamorthy"
)
```

### Step 7: Verify

```
mcp__gitkraken__git_log_or_diff(directory: ".", action: "log")
```

Confirm the commit appears with the correct message format.

### Step 8: Push to remote

Always push after committing. Use `--force-with-lease` after rebasing (Step 1 already ensured the branch is up to date). Do not ask the user — just push.

```
mcp__gitkraken__git_push(directory: ".")
```

---

## Creating a Pull Request

When the user asks to create a PR, review all commits on the branch and generate a comprehensive PR description.

### Step 1: Identify the base branch

```bash
git merge-base origin/main HEAD
```

### Step 2: Review all commits since diverging from main

```
mcp__gitkraken__git_log_or_diff(directory: ".", action: "log", revision_range: "origin/main..HEAD")
```

Read every commit message — not just the latest one. Each commit's `Area | Change` table is your source of truth.

### Step 3: Review the full diff

```
mcp__gitkraken__git_log_or_diff(directory: ".", action: "diff", revision_range: "origin/main..HEAD")
```

### Step 4: Compose the PR description

Build the PR using this template:

```markdown
## Summary

[2-3 sentences: what this PR does at a high level and why]

## Changes

| Area | Change |
|------|--------|
| [file/module] | [what changed — aggregated from all commits] |
| ... | ... |

## Commits

- `abc1234` type(scope): description
- `def5678` type(scope): description
- ...

## Test Plan

- [ ] Unit tests pass (`uv run pytest src/test/unit/ -q`)
- [ ] [Any specific manual verification steps]
- [ ] No regressions in existing features
```

### Aggregation rules

- **Merge related changes** — If multiple commits touched the same file, combine them into one row in the Changes table with a summary of the net effect.
- **High-level summary first** — The Summary section should explain the "why" and overall intent, not list individual commits.
- **Preserve commit history** — List every commit hash and message in the Commits section so reviewers can trace the history.
- **PR title** — Derive from the overall theme. If all commits share a scope, use `type(scope): high-level description`. Keep under 70 characters.

### Step 5: Create the PR

```bash
gh pr create --title "type(scope): high-level description" --body "..."
```

Use a HEREDOC for the body to preserve formatting.

---

## Common Mistakes to Avoid

| Mistake | Why It's Wrong | Correct Approach |
|---------|---------------|-----------------|
| `feat: add login` | Missing scope | `feat(auth): add login endpoint` |
| `Updated files` | Too vague | Describe the specific change per file |
| Missing table rows | Incomplete record | Every staged file gets a row |
| `feat(auth): Added login` | Past tense | Use imperative: `add`, not `Added` |
| Summary says "modified" | Doesn't explain what changed | Describe the actual modification |
| No blank line after header | Breaks git formatting | Always blank line between header and body |
| Table without header row | Invalid markdown table | Always include `| Area | Change |` and `|---|---|` |
| Line > 72 chars in header | Breaks git log formatting | Keep first line under 72 characters |

---

## Pre-Commit Verification

Before committing, verify:
- [ ] Branch is rebased onto latest `origin/main` (`git fetch origin && git rebase origin/main`)
- [ ] All staged files are intentional (reviewed via `git_log_or_diff` diff)
- [ ] No secrets or `.env` files in the staged changes
- [ ] Tests pass (`uv run pytest src/test/unit/ -q`)
- [ ] Lint passes (`uv run pylint src/budget_analyser`)
- [ ] Commit message follows the `type(scope): description` format
- [ ] File-change table uses `| Area | Change |` columns
- [ ] Author trailer is `Author: Prabhukumar Sivamorthy`
