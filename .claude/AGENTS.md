# Budget Analyser — Team Collaboration Model

## Teams

### Planning Team

| Agent | Role | Model | MCP Servers |
|-------|------|-------|-------------|
| **Software Architect** (lead) | Architecture decisions, design orchestration | opus | github, context7 |
| **Finance Analyst** | Domain validation, financial logic review | opus | sqlite, context7 |

### Implementation Team

| Agent | Role | Model | MCP Servers |
|-------|------|-------|-------------|
| **UI/UX Engineer** | Design, layout, accessibility, financial UX | sonnet | github, context7, ide |
| **Frontend Engineer** | React/Tauri/TypeScript implementation | sonnet | github, context7, ide |
| **Backend Engineer** | Python/FastAPI/pandas implementation | sonnet | github, sqlite, context7 |

### Quality Team

| Agent | Role | Model | MCP Servers |
|-------|------|-------|-------------|
| **Pytest Engineer** (lead) | Unit + integration tests | sonnet | sqlite, context7 |
| **Playwright Engineer** | E2E browser tests | sonnet | playwright, github, context7 |
| **Code Reviewer** | Final review gate (read-only) | sonnet | — |

### Cross-cutting

| Agent | Role | Model | MCP Servers |
|-------|------|-------|-------------|
| **Release Engineer** | Build, CI/CD, releases | sonnet | github, context7 |

---

## Collaboration Protocol

### Phase 1: Round-table Discussion

When a new task arrives, the Software Architect initiates a round-table:

```
New Task
  │
  ├── Software Architect    → Proposes design approach, identifies components
  ├── Finance Analyst       → Validates domain logic, flags financial edge cases
  ├── Frontend Engineer     → Flags UI complexity, estimates frontend effort
  ├── Backend Engineer      → Flags data/API complexity, estimates backend effort
  │
  └── Consensus → Brief design decision + task breakdown
```

**Participation rules:**
- Software Architect: ALWAYS participates
- Finance Analyst: Joins when task touches financial logic, categories, budgets, reports, forecasting, or transaction data
- UI/UX Engineer: Joins when task involves layout, design, accessibility, or financial data presentation
- Frontend Engineer: Joins when task involves UI changes or new pages
- Backend Engineer: Joins when task involves API, service, model, or data changes
- Pytest/Playwright Engineers: Join when task has significant testability implications

**Round-table output:** Design decision document with:
- Agreed approach and rationale
- Task breakdown per agent
- Identified risks and mitigations
- Dependencies between tasks

### Phase 2: Parallel Dispatch

After consensus, implementation agents work simultaneously:

```
Design Decision
  │
  ├── UI/UX Engineer    ──→ Layout specs, component design, accessibility (first)
  │
  ├── Frontend Engineer ──→ React components, pages, hooks (worktree A)
  │
  ├── Backend Engineer  ──→ Vertical slice: models.py + service.py + router (worktree B)
  │
  └── FE + BE work independently, merge when complete
```

**Rules:**
- Use isolated git worktrees when both agents modify code
- Each agent follows the approved design — no freelancing
- Flag deviations immediately rather than proceeding with unapproved changes

### Phase 3: Quality Pipeline

Sequential validation after implementation:

```
Implementation Complete
  │
  ├── 1. Pytest Engineer     → Unit tests + integration tests
  │                            Run: uv run pytest src/test/unit/ -q
  │
  ├── 2. Playwright Engineer → E2E browser tests
  │                            Run: cd src/frontend && npm run test:e2e
  │
  └── 3. Code Reviewer       → Final review gate
                                Verdict: APPROVE or REQUEST CHANGES
```

**Quality gate rules:**
- All unit tests must pass before E2E testing begins
- Code Reviewer review is MANDATORY for every implementation task
- REQUEST CHANGES blocks merge until issues are resolved

---

## Mandatory Review Matrix

| Change Type | Finance Analyst | Code Reviewer | Pytest Engineer | Playwright Engineer |
|-------------|:-:|:-:|:-:|:-:|
| Financial calculations | REQUIRED | REQUIRED | REQUIRED | — |
| Budget/category logic | REQUIRED | REQUIRED | REQUIRED | — |
| Forecasting/trends | REQUIRED | REQUIRED | REQUIRED | — |
| API endpoints | — | REQUIRED | REQUIRED | REQUIRED |
| React pages/components | — | REQUIRED | — | REQUIRED |
| Database schema | REQUIRED | REQUIRED | REQUIRED | — |
| CSV ingestion | REQUIRED | REQUIRED | REQUIRED | REQUIRED |
| Configuration/settings | — | REQUIRED | REQUIRED | — |
| CI/CD/build | — | REQUIRED | — | — |

---

## Universal Standards

All agents MUST:

1. **Read CLAUDE.md** before starting any work
2. **Follow vertical slices** architecture pattern
3. **Write Google-style docstrings** on all public functions and classes
4. **Add type hints** on all function signatures
5. **Use `from __future__ import annotations`** in every Python module
6. **Create signed semantic commits** with file-change tables
7. **Respect max line length** of 100 characters
8. **Use keyword-only arguments** for clarity (`def foo(*, arg1, arg2)`)

---

## Agent Roster

| Agent File | Identity | Autonomy |
|------------|----------|----------|
| `agents/finance-analyst.md` | Domain expert + SQL data analyst | Read-only + SQL queries |
| `agents/software-architect.md` | Budget Analyser-aware architect | Read-only analysis |
| `agents/uiux-engineer.md` | UI/UX design + accessibility specialist | Full read/write |
| `agents/frontend-engineer.md` | React/Tauri/TypeScript specialist | Full read/write |
| `agents/backend-engineer.md` | Python/FastAPI/pandas specialist | Full read/write |
| `agents/pytest-engineer.md` | Unit/integration test specialist | Full read/write |
| `agents/playwright-engineer.md` | E2E browser test specialist | Full read/write |
| `agents/release-engineer.md` | Build + CI/CD + releases | Read + build commands |
