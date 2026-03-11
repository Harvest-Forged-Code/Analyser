# Design: Budget Analyser Agents, Skills & Hooks

**Date:** 2026-03-10
**Status:** Approved

## Summary

Create a comprehensive development team of specialized Claude Code agents, skills, and hooks for the Budget Analyser project. The system uses a round-table + hybrid collaboration model with 3 teams (Planning, Implementation, Quality).

## Agents (7 new)

| Agent | Role | Model | MCP Servers |
|-------|------|-------|-------------|
| `finance-analyst` | Domain expert + SQL data analyst | opus | sqlite, context7 |
| `software-architect` | Budget Analyser-aware architect | opus | github, context7 |
| `frontend-engineer` | React/Tauri/TypeScript specialist | sonnet | github, context7, ide |
| `backend-engineer` | Python/FastAPI/pandas specialist | sonnet | github, sqlite, context7 |
| `pytest-engineer` | Unit/integration test specialist | sonnet | sqlite, context7 |
| `playwright-engineer` | E2E browser testing specialist | sonnet | playwright, github, context7 |
| `release-engineer` | Tauri build + CI/CD + releases | sonnet | github, context7 |

## Team Model

### Teams
- **Planning Team:** Software Architect (lead) + Finance Analyst
- **Implementation Team:** Frontend Engineer + Backend Engineer
- **Quality Team:** Pytest Engineer (lead) + Playwright Engineer + Code Reviewer (existing)
- **Cross-cutting:** Release Engineer

### Workflow
1. **Round-table** — Planning team + relevant implementation agents discuss task, reach consensus
2. **Parallel dispatch** — Frontend + Backend work simultaneously in isolated worktrees
3. **Quality pipeline** — Pytest → Playwright → Code Reviewer (sequential)

## Skills (3 new)

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `team-roundtable` | `/team-roundtable` | Orchestrate round-table discussion and dispatch |
| `financial-review` | `/financial-review` | Finance Analyst reviews financial logic |
| `release-build` | `/release-build` | Full build + release pipeline |

## Hooks (7 new)

| Hook | Trigger | Type |
|------|---------|------|
| `pylint-gate.sh` | PreToolUse (git commit) | Blocker |
| `type-check.sh` | PreToolUse (git commit) | Blocker |
| `frontend-lint.sh` | PreToolUse (git commit) | Blocker |
| `test-gate.sh` | PreToolUse (git commit) | Blocker |
| `docstring-check.sh` | PostToolUse (Write/Edit .py) | Warning |
| `large-file-guard.sh` | PreToolUse (Write) | Blocker |
| `prompt-injection-guard.sh` | PreToolUse (Write/Edit) | Warning |

## Hook Execution Order (on git commit)

1. sensitive-file-guard.sh
2. pre-commit-lint.sh (ruff)
3. pylint-gate.sh (pylint >= 8.0)
4. frontend-lint.sh (ESLint + tsc)
5. type-check.sh (pyright)
6. test-gate.sh (pytest)
7. pre-commit-security.sh

## Modified Files

- `.claude/settings.json` — Register new hooks
- `.claude/hooks.json` — Hook event bindings
- `.claude/hooks/sensitive-file-guard.sh` — Extended patterns (.sqlite, API keys in TSX, hardcoded ports)
