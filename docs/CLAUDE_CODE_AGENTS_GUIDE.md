# Claude Code Agents & Subagents Guide

This guide covers how to create custom agents, add skills, and configure tool access in Claude Code.

## Table of Contents

- [What Are Agents/Subagents?](#what-are-agentssubagents)
- [Built-in Agent Types](#built-in-agent-types)
- [Creating Custom Agents](#creating-custom-agents)
- [Configuration Fields Reference](#configuration-fields-reference)
- [Adding Skills to Agents](#adding-skills-to-agents)
- [Configuring Tool Access](#configuring-tool-access)
- [Running Agents in Background](#running-agents-in-background)
- [Resuming Agents](#resuming-agents)
- [Storage Locations](#storage-locations)
- [Practical Examples](#practical-examples)
- [Best Practices](#best-practices)

---

## What Are Agents/Subagents?

Subagents are specialized AI assistants that handle specific tasks independently. Each runs in its own isolated context with:

- Custom system prompt tailored to its purpose
- Specific tool access (can be restricted)
- Independent permissions
- Ability to work separately from your main conversation

**Key Benefits:**

- Preserve context by keeping exploration and implementation separate
- Enforce constraints by limiting tool access
- Reuse configurations across projects
- Specialize behavior for specific domains
- Control costs by routing tasks to faster models (like Haiku)

---

## Built-in Agent Types

| Agent | Model | Tools | Best For |
|-------|-------|-------|----------|
| **Explore** | Haiku (fast) | Read-only | File discovery, code search, codebase exploration |
| **Plan** | Inherited | Read-only | Research during plan mode before implementation |
| **General-purpose** | Inherited | All tools | Complex multi-step tasks requiring exploration + action |
| **Bash** | Inherited | Bash only | Terminal commands in separate context |

### When to Use Which Agent

| Agent | Use When | Example |
|-------|----------|---------|
| **Explore** | Need to search codebase without changes | "Find files handling authentication" |
| **Plan** | Planning complex refactors safely | "Create a migration plan for OAuth2" |
| **General-purpose** | Complex multi-step work | "Implement and test a new feature" |
| **Main conversation** | Frequent iteration needed | "Let's build this together incrementally" |
| **Background agent** | Task produces verbose output | "Run tests - only report failures" |

---

## Creating Custom Agents

### Method 1: Interactive Command (Recommended)

```bash
/agents
```

Follow the guided prompts to:
1. View all available agents (built-in, user, project, plugin)
2. Create new agents with guided setup or Claude generation
3. Edit existing agent configurations
4. Delete custom agents

### Method 2: Manual File Creation

Create agent definition files as Markdown with YAML frontmatter.

**Project-level agent** (shared with team):
```
.claude/agents/my-agent/AGENT.md
```

**User-level agent** (available in all your projects):
```
~/.claude/agents/my-agent/AGENT.md
```

**Example agent file:**

```markdown
---
name: code-reviewer
description: Expert code reviewer. Use when reviewing code changes.
tools: Read, Grep, Glob, Bash
model: sonnet
permissionMode: default
skills:
  - coding-standards
color: blue
---

You are a senior code reviewer. When invoked:
1. Run git diff to see changes
2. Review for quality, security, maintainability
3. Provide prioritized feedback

Review checklist:
- Code is clear and readable
- Functions and variables are well-named
- No duplicated code
- Proper error handling
- No exposed secrets or API keys
```

### Method 3: CLI Flag (Temporary Session)

```bash
claude --agents '{
  "my-agent": {
    "description": "When to use this agent",
    "prompt": "System prompt here",
    "tools": ["Read", "Bash"],
    "model": "sonnet"
  },
  "another-agent": {
    "description": "Another agent description",
    "prompt": "Another system prompt",
    "tools": ["Read", "Edit", "Bash"],
    "model": "haiku"
  }
}'
```

**Note:** CLI-defined agents only exist for that session.

---

## Configuration Fields Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Unique identifier using lowercase letters and hyphens (e.g., `code-reviewer`) |
| `description` | String | Natural language description of when Claude should use this agent |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tools` | String/Array | Inherits all | Comma-separated list or array of allowed tools |
| `disallowedTools` | String/Array | None | Tools to explicitly deny |
| `model` | String | `inherit` | Model: `sonnet`, `opus`, `haiku`, or `inherit` |
| `permissionMode` | String | `default` | Permission handling mode |
| `skills` | Array | None | Array of skill names to preload |
| `hooks` | Object | None | Lifecycle hooks (PreToolUse, PostToolUse, Stop) |
| `color` | String | None | Display color for the agent UI |

### Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Asks for permission before file edits |
| `acceptEdits` | Auto-accepts file edits without asking |
| `dontAsk` | Auto-denies permission prompts |
| `bypassPermissions` | Skips all permission checks (use with caution) |
| `plan` | Read-only mode (plan mode) |

### Model Options

| Model | Description |
|-------|-------------|
| `sonnet` | Balanced capability and speed (recommended for most tasks) |
| `opus` | Most capable, best for complex reasoning |
| `haiku` | Fastest and cheapest |
| `inherit` | Same as main conversation (default) |

---

## Adding Skills to Agents

Skills extend agent capabilities by injecting specialized knowledge.

### Step 1: Create a Skill File

Create `.claude/skills/my-skill/SKILL.md`:

```markdown
---
name: financial-terminology
description: Financial terms reference for budget analysis
user-invocable: false
---

## Transaction Types
- **Income**: Deposits, salary, refunds, interest
- **Expenses**: Purchases, fees, transfers out
- **Transfers**: Internal account movements

## Budget Terms
- **Allocated Budget**: Monthly spending limit per category
- **Actual Spending**: Transactions categorized in this period
- **Variance**: Difference between allocated and actual
- **Burn Rate**: Speed of spending vs budget
```

### Step 2: Reference in Agent

```markdown
---
name: finance-analyst
description: Financial analyst for transaction analysis
tools: Read, Bash, Grep, Glob
skills:
  - financial-terminology
  - data-analysis-patterns
---

When analyzing, refer to the preloaded skills for terminology...
```

The skill content is **automatically injected** into the agent's context at startup.

### Two Patterns for Using Skills

**Pattern 1: Preload into Context**

Add skills to the `skills` array - full content is injected at startup:

```markdown
---
skills:
  - api-conventions
  - error-handling-patterns
---
```

**Pattern 2: Agent Invokes Skills During Execution**

Allow the agent to call skills by including `Skill` in the tools list:

```markdown
---
tools: Read, Edit, Bash, Skill
---

When needed, invoke skills using /skill-name format...
```

---

## Configuring Tool Access

### Available Tools

| Tool | Description | Typical Use |
|------|-------------|-------------|
| `Read` | Read file contents | Exploration, analysis |
| `Grep` | Search in files | Pattern matching |
| `Glob` | Find files by pattern | File discovery |
| `Bash` | Execute shell commands | Running tests, scripts |
| `Write` | Create/overwrite files | Generating code, config |
| `Edit` | Make targeted edits | Modifying existing files |
| `WebFetch` | Fetch URLs | External documentation |
| `WebSearch` | Web search | Research |
| `Skill` | Execute skills | Delegating to skills |
| `Task` | Run subagents | Complex workflows |

### Method A: Allowlist (Recommended)

Specify exactly which tools the agent can use:

```markdown
---
tools: Read, Grep, Glob, Bash
---
```

This agent can **only** use Read, Grep, Glob, and Bash.

### Method B: Denylist

Start with all tools, then explicitly deny specific ones:

```markdown
---
tools: Read, Edit, Write, Bash, Grep, Glob
disallowedTools: WebSearch, WebFetch
---
```

### Method C: Hooks for Fine-Grained Control

Use `PreToolUse` hooks for validation:

```markdown
---
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh"
---
```

Example validation script (`scripts/validate-readonly-query.sh`):

```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Block write operations
if echo "$COMMAND" | grep -iE '\b(INSERT|UPDATE|DELETE|DROP)\b' > /dev/null; then
  echo "Blocked: Only SELECT queries are allowed" >&2
  exit 2
fi

exit 0
```

### Project-Level Permission Restrictions

In `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(pytest:*)",
      "Bash(python3:*)",
      "Read(./src/**)",
      "Write(./src/**)"
    ],
    "deny": [
      "Bash(rm:*)",
      "Read(./.env)",
      "WebSearch"
    ]
  }
}
```

---

## Running Agents in Background

### Two Methods

1. Say `"Run this in the background"`
2. Press **Ctrl+B** during task execution

### Background vs Foreground

| Aspect | Foreground (Default) | Background |
|--------|---------------------|------------|
| Blocking | Yes | No |
| Permission prompts | Interactive | Auto-denied if not pre-approved |
| MCP tools | Available | Not available |
| Use case | Interactive work | Verbose output, parallel tasks |

### Disable Background Tasks

```bash
export CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1
```

---

## Resuming Agents

Each agent invocation returns an `agentId`. To continue previous work:

```
Continue that code review and now analyze the authorization logic
```

**Key Points:**
- Resumed agents retain full conversation history
- All previous tool calls and results preserved
- Picks up exactly where it stopped
- Transcripts stored at: `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`

---

## Storage Locations

| Location | Scope | Priority | Who Sees It |
|----------|-------|----------|-------------|
| `--agents` CLI flag | Current session only | 1 (highest) | Only this session |
| `.claude/agents/` | Project-level | 2 | All team members (git) |
| `~/.claude/agents/` | User-level | 3 | All your projects |
| Plugin's `agents/` | Plugin scope | 4 (lowest) | Where plugin enabled |

**When multiple agents have the same name:** Higher priority location wins.

### Recommended Structure

```
project/
├── .claude/
│   ├── agents/
│   │   └── my-agent/
│   │       ├── AGENT.md
│   │       └── supporting-files/
│   │           ├── best-practices.md
│   │           └── examples/
│   └── skills/
│       └── my-skill/
│           └── SKILL.md
└── ...
```

---

## Practical Examples

### Example 1: Read-Only Code Reviewer

```markdown
---
name: code-reviewer
description: Expert code reviewer. Use after writing or modifying code.
tools: Read, Grep, Glob, Bash
model: inherit
color: blue
---

You are a senior code reviewer. When invoked:
1. Run `git diff` to see recent changes
2. Focus on modified files
3. Begin review immediately

Review checklist:
- Code is clear and readable
- No duplicated code
- Proper error handling
- No exposed secrets
- Adequate test coverage

Provide feedback by priority:
- **Critical** (must fix)
- **Warnings** (should fix)
- **Suggestions** (consider)
```

### Example 2: Debugger with Edit Access

```markdown
---
name: debugger
description: Debugging specialist for errors and test failures.
tools: Read, Edit, Bash, Grep, Glob
model: inherit
---

You are an expert debugger. When invoked:
1. Capture error message and stack trace
2. Identify reproduction steps
3. Isolate the failure location
4. Implement minimal fix
5. Verify solution works

For each issue, provide:
- Root cause explanation
- Specific code fix
- Testing approach
```

### Example 3: Finance Analyst (Project-Specific)

```markdown
---
name: finance-analyst
description: Financial analyst for transaction analysis and budget reporting.
tools: Read, Bash, Grep, Glob
disallowedTools: WebSearch, WebFetch
model: sonnet
skills:
  - financial-terminology
  - budget-analysis-patterns
color: green
---

You are a financial data analyst for the Budget Analyser application.

When analyzing transactions:
1. Query the SQLite database
2. Use pandas for data manipulation
3. Follow the project's layered architecture

Focus on:
- Transaction categorization accuracy
- Spending pattern identification
- Budget goal tracking
- Trend analysis
```

### Example 4: Database Query Validator

```markdown
---
name: db-reader
description: Execute read-only database queries.
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
---

You are a database analyst with read-only access.
Execute SELECT queries to answer data questions.
```

---

## Best Practices

### Design Principles

1. **One purpose per agent** - Each agent should excel at one task
2. **Write detailed descriptions** - Claude uses descriptions to decide when to delegate
3. **Limit tool access** - Grant only necessary permissions
4. **Use appropriate models** - Haiku for speed, Opus for complex reasoning

### Context Management

- Subagents cannot spawn other subagents (use chaining instead)
- Use background agents for verbose output
- Preload skills for domain knowledge

### Workflow Patterns

**Isolate High-Volume Operations:**
```
Use a subagent to run tests and report only failures
```

**Parallel Research:**
```
Research the auth, database, and API modules in parallel using separate subagents
```

**Chain Subagents:**
```
Use the code-reviewer to find issues, then use the fixer to resolve them
```

---

## Quick Reference

### Commands

```bash
# View/manage agents
/agents

# Use an agent
"Use the budget-analyst agent to analyze spending trends"

# Run in background
"Run this in the background" or Ctrl+B

# Resume agent
"Continue that investigation..."
```

### File Locations

| Type | Location |
|------|----------|
| Project agents | `.claude/agents/name/AGENT.md` |
| User agents | `~/.claude/agents/name/AGENT.md` |
| Project skills | `.claude/skills/name/SKILL.md` |
| User skills | `~/.claude/skills/name/SKILL.md` |
| Settings | `.claude/settings.json` |

### Minimal Agent Template

```markdown
---
name: my-agent
description: When to use this agent
tools: Read, Grep, Glob, Bash
model: sonnet
---

Your system prompt here...
```

### Full Agent Template

```markdown
---
name: my-agent
description: Detailed description of when Claude should use this agent
tools: Read, Grep, Glob, Bash, Edit, Write
disallowedTools: WebSearch
model: sonnet
permissionMode: default
skills:
  - skill-one
  - skill-two
color: blue
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./validate.sh"
---

You are a specialized agent for [purpose].

When invoked:
1. First step
2. Second step
3. Third step

Focus on:
- Key area 1
- Key area 2
```