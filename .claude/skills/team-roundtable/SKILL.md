---
name: team-roundtable
description: Orchestrate a round-table discussion with the Budget Analyser development team agents before implementing a feature or task
---

# Team Round-table Discussion

Orchestrate a collaborative design discussion among specialist agents before implementation begins. This ensures architectural alignment, domain validation, and clear task breakdown.

## When to Use

- New feature development involving multiple layers (frontend + backend)
- Changes to financial logic that need domain validation
- Architectural decisions affecting multiple feature modules
- Any task where you are unsure which agents should be involved

## Process

### Step 1: Analyze the Task

Read the task description and determine scope:
- Does it touch financial logic? → Finance Analyst must participate
- Does it involve UI layout, design, or accessibility? → UI/UX Engineer joins
- Does it involve UI changes? → Frontend Engineer joins
- Does it involve API/service/data changes? → Backend Engineer joins
- Does it affect E2E user workflows? → Playwright Engineer weighs in
- Does it have significant test implications? → Pytest Engineer joins

### Step 2: Spawn Round-table Agents in Parallel

Launch the **Software Architect** agent (always) and relevant specialist agents simultaneously. Each agent receives the task description and answers:

1. **Proposed approach** — How would you tackle this from your domain?
2. **Risks and concerns** — What could go wrong from your perspective?
3. **Dependencies** — What do you need from other agents?
4. **Effort estimate** — How complex is your portion?

Use the Agent tool with these agent definitions:
- `software-architect` — Architecture design, component analysis
- `finance-analyst` — Domain validation (if financial logic involved)
- `uiux-engineer` — Design, layout, accessibility (if UI involved)
- `frontend-engineer` — UI feasibility (if UI changes involved)
- `backend-engineer` — API/data feasibility (if backend changes involved)

### Step 3: Synthesize Consensus

After all agents return, the orchestrator (you) must:

1. **Identify agreements** — Where do agents align?
2. **Resolve conflicts** — If agents disagree, favor:
   - Finance Analyst on financial correctness
   - Software Architect on architecture decisions
   - Implementation agents on technical feasibility
3. **Create design decision** — Brief summary of the agreed approach
4. **Define task breakdown** — What each agent will implement

### Step 4: Dispatch Implementation

Based on the consensus:

```
Frontend Engineer ──→ React pages, components, hooks  (parallel)
Backend Engineer  ──→ Vertical slice: models + service + router  (parallel)
```

- Use `isolation: "worktree"` when both agents modify code simultaneously
- Each agent gets the design decision and their specific task list

### Step 5: Quality Gate

After implementation completes:

```
1. Pytest Engineer    → Write/run unit + integration tests
2. Playwright Engineer → Write/run E2E tests (if UI was changed)
3. Code Reviewer      → Final review (use code-reviewer subagent)
```

## Output Template

After the round-table, present this summary:

```markdown
## Round-table Decision: [Task Title]

### Participants
- Software Architect: [key insight]
- Finance Analyst: [key insight] (if participated)
- Frontend Engineer: [key insight] (if participated)
- Backend Engineer: [key insight] (if participated)

### Agreed Approach
[2-3 sentences describing the consensus design]

### Task Breakdown
| Task | Agent | Priority | Dependencies |
|------|-------|----------|-------------|
| ... | ... | ... | ... |

### Risks Identified
- [Risk 1 and mitigation]
- [Risk 2 and mitigation]

### Quality Plan
- Unit tests: [what to test]
- E2E tests: [what workflows to verify]
- Review focus: [what the reviewer should pay attention to]
```

## Rules

- Software Architect ALWAYS participates — no exceptions
- Finance Analyst is MANDATORY for any financial logic changes
- Never skip the round-table for multi-agent tasks
- Keep the discussion focused — 2-3 key questions per agent, not open-ended exploration
- The round-table should take minutes, not hours — if it is taking too long, the task needs to be decomposed
