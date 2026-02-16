# ---
# name: documentation-generator
# description: >
#   Use when generating or updating project documentation — README files,
#   API reference docs, architecture decision records (ADRs), architecture
#   overviews, onboarding guides, and inline code documentation.
# trigger: >
#   When user asks for documentation, README, API docs, architecture docs,
#   ADRs, onboarding guides, or mentions that docs are missing or outdated.
# references: []
# ---

# Documentation Generator Skill

## Purpose

Generate accurate, comprehensive, and maintainable project documentation by
exploring the actual codebase. All documentation must reflect the real state
of the code — never guess, never fabricate, never document aspirational
features that do not exist yet.

## Workflow — Follow Each Step in Order

### Step 1: Explore the Codebase

Before writing any documentation, build a thorough understanding of the
project:

1. **Project structure**: Map the directory tree, identify source directories,
   test directories, configuration files, and build artifacts
2. **Main modules**: Identify the core packages/modules and their
   responsibilities
3. **Entry points**: Find how the application starts — main files, CLI
   commands, server entry points, Lambda handlers
4. **Dependencies**: Read `requirements.txt`, `pyproject.toml`, `package.json`,
   `go.mod`, `Cargo.toml`, or equivalent to understand external dependencies
5. **Configuration**: Identify environment variables, config files, feature
   flags, and their defaults
6. **Existing documentation**: Check for existing README, docs directory, wiki,
   docstrings, and inline comments — understand what already exists and what
   is outdated

### Step 2: Identify What Documentation Is Needed

Based on the codebase exploration and user request, determine which
documentation artifacts to create or update:

| Doc Type               | When Needed                                                  |
|------------------------|--------------------------------------------------------------|
| **README**             | Always — every project needs one                             |
| **API Reference**      | When project exposes HTTP/gRPC/GraphQL APIs                  |
| **Architecture Overview** | When project has 3+ services or complex module structure  |
| **ADR**                | When a significant technical decision was made               |
| **Onboarding Guide**   | When project has complex setup or multiple contributors      |
| **Runbook**            | When project runs in production and has operational concerns  |
| **Changelog**          | When project has releases and users need migration guidance   |

### Step 3: Generate README

If a README is needed, include these sections in order:

```markdown
# Project Name

One-paragraph description: what the project does, who it is for, and why
it exists.

## Prerequisites

- Runtime version (e.g., Python 3.11+, Node 20+)
- Required system dependencies
- Required external services (database, cache, message broker)

## Installation

Step-by-step commands to install the project from scratch.
Include both development and production installation paths.

## Configuration

Table of environment variables / config options:

| Variable         | Required | Default   | Description                  |
|------------------|----------|-----------|------------------------------|
| DATABASE_URL     | Yes      | —         | PostgreSQL connection string |
| REDIS_URL        | No       | localhost | Redis connection string      |
| LOG_LEVEL        | No       | INFO      | Logging verbosity            |

## Usage

### Running Locally

Commands to start the application for local development.

### Running Tests

Commands to run the test suite with expected output.

### Common Tasks

Frequent developer tasks: migrations, seeding, linting, building.

## Project Structure

Brief description of the directory layout and what each top-level
directory contains.

## Deployment

How to deploy: CI/CD pipeline, manual steps, infrastructure requirements.

## Contributing

Branching strategy, PR process, code review expectations, coding standards.

## License

License type and link to LICENSE file.
```

**Rules for README:**
- Every command must be copy-pasteable and actually work
- Do not include commands you have not verified
- Use the project's actual names, paths, and ports
- Keep it concise — link to detailed docs instead of embedding everything

### Step 4: Generate API Documentation

If the project exposes an API, generate reference documentation:

1. **Check for existing OpenAPI/Swagger spec**: If one exists, use it as the
   source of truth; update it if it is outdated
2. **If no spec exists, generate from code**:
   - Scan route definitions / controller files
   - Extract endpoint path, method, parameters, request body, response schema
   - Extract authentication requirements
   - Extract rate limiting or quota information
3. **For each endpoint, document**:

```markdown
### GET /api/v1/users/{id}

Retrieve a user by their unique identifier.

**Authentication:** Bearer token required

**Path Parameters:**

| Parameter | Type   | Required | Description        |
|-----------|--------|----------|--------------------|
| id        | string | Yes      | User UUID          |

**Query Parameters:**

| Parameter | Type    | Required | Default | Description         |
|-----------|---------|----------|---------|---------------------|
| include   | string  | No       | —       | Comma-separated relations to include |

**Response 200:**

​```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Alice",
  "email": "alice@example.com",
  "created_at": "2025-01-15T10:30:00Z"
}
​```

**Response 404:**

​```json
{
  "error": "not_found",
  "message": "User not found"
}
​```
```

4. **Add runnable examples**: Provide curl commands or code snippets that
   developers can execute immediately against a local or staging environment

### Step 5: Generate Architecture Documentation

If architecture documentation is needed:

1. **System overview diagram**: Create a text-based or Mermaid diagram showing
   all major components and their interactions

```markdown
## System Architecture

​```mermaid
graph TD
    Client[Web Client] --> API[API Gateway]
    API --> Auth[Auth Service]
    API --> Users[User Service]
    API --> Orders[Order Service]
    Orders --> DB[(PostgreSQL)]
    Orders --> Queue[RabbitMQ]
    Queue --> Worker[Background Worker]
    Worker --> Email[Email Service]
​```
```

2. **Component descriptions**: For each component, document:
   - Responsibility (what it does)
   - Technology (what it is built with)
   - Inputs and outputs (what it receives and produces)
   - Dependencies (what it depends on)
   - Scaling characteristics (stateless/stateful, horizontal/vertical)

3. **Data flow**: Document how data moves through the system for key
   operations (e.g., user registration, order placement, report generation)

4. **Infrastructure**: Document deployment topology, networking, storage,
   and monitoring

### Step 6: Generate Architecture Decision Records (ADRs)

For each significant technical decision, create an ADR following this template:

```markdown
# ADR-NNN: [Short Title of Decision]

## Status

[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Date

YYYY-MM-DD

## Context

What is the issue that we are seeing that is motivating this decision or
change? Describe the technical context, constraints, and forces at play.

## Decision

What is the change that we are proposing and/or doing? State the decision
clearly and concisely.

## Consequences

### Positive
- What becomes easier or possible as a result of this decision?

### Negative
- What becomes harder or impossible as a result of this decision?
- What technical debt does this introduce?

### Neutral
- What other effects does this decision have?

## Alternatives Considered

### Alternative 1: [Name]
- Description: ...
- Pros: ...
- Cons: ...
- Why rejected: ...

### Alternative 2: [Name]
- Description: ...
- Pros: ...
- Cons: ...
- Why rejected: ...
```

**Rules for ADRs:**
- One decision per ADR
- ADRs are immutable once accepted — if a decision changes, create a new ADR
  that supersedes the old one
- Number ADRs sequentially (ADR-001, ADR-002, ...)
- Store ADRs in `docs/adr/` or `docs/decisions/`

### Step 7: Write Clear, Concise Documentation

Apply these writing principles to all documentation:

- **Use active voice**: "The service processes orders" not "Orders are
  processed by the service"
- **Be specific**: "Responds within 200ms at p95" not "Responds quickly"
- **Use consistent terminology**: Pick one term for each concept and use it
  everywhere (do not alternate between "user", "account", "customer" for the
  same entity)
- **Keep paragraphs short**: 3-4 sentences maximum
- **Use headings, tables, and lists**: Scannable structure over prose
- **Write for the reader**: Assume a new team member reading for the first time

### Step 8: Add Code Examples That Actually Run

Every code example in documentation must be:

1. **Complete**: Include all imports, setup, and teardown needed to run
2. **Correct**: Copy-paste from docs into a file and it runs without errors
3. **Current**: Uses the actual API as it exists today, not a planned version
4. **Minimal**: Shows only what is needed to illustrate the concept

```python
# GOOD: Complete, runnable example
from myproject import create_app, db

app = create_app()
with app.app_context():
    user = db.session.query(User).filter_by(email="alice@example.com").first()
    print(f"Found user: {user.name}")

# BAD: Incomplete, will not run
user = get_user("alice@example.com")  # where does get_user come from?
```

### Step 9: Verify Documentation

Run through this verification checklist:

1. **Commands work**: Execute every shell command in the documentation and
   confirm it succeeds
2. **Links are valid**: Check that all internal links point to existing files
   and all external links resolve
3. **Examples run**: Copy each code example into a file and execute it
4. **Information is current**: Cross-reference documented configuration,
   endpoints, and structures against the actual code
5. **No placeholders left**: Search for TODO, FIXME, TBD, XXX, "insert here",
   or any placeholder text
6. **Consistent formatting**: Headings, code blocks, tables, and lists follow
   a consistent style throughout

### Step 10: Final Checklist

Before marking documentation as complete, verify:

- [ ] README exists and contains all required sections
- [ ] API documentation is current and matches actual endpoints
- [ ] Architecture is documented with diagrams and component descriptions
- [ ] Key technical decisions are recorded as ADRs
- [ ] All commands in documentation actually work when executed
- [ ] All links (internal and external) are valid
- [ ] All code examples run without modification
- [ ] Documentation uses consistent terminology and formatting
- [ ] No placeholder text remains (TODO, TBD, FIXME)
- [ ] Documentation is stored in a logical location (README at root,
      detailed docs in `docs/` directory)

## Enforced Standards

### Google-Style Docstrings (MANDATORY)
Every function, method, and class written or modified during documentation generation MUST have a Google-style docstring. No exceptions. This includes:
- One-line summary in imperative mood
- Args section for all parameters
- Returns section describing what is returned
- Raises section for all exceptions
- See CLAUDE.md [STANDARDS] for full specification and examples.

### Git Commit Format (MANDATORY)
All commits created during documentation generation MUST follow this format:
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

## Anti-Patterns to Avoid

- **Aspirational docs**: Do not document features that do not exist yet
- **Copy-paste from other projects**: Do not reuse docs from other projects
  without verifying accuracy for this project
- **Over-documentation**: Do not document obvious things; focus on what a
  new developer would actually need to know
- **Under-documentation**: Do not skip configuration, environment setup, or
  deployment — these are the most common sources of confusion
- **Stale examples**: Do not leave examples that reference old APIs, removed
  endpoints, or deprecated configuration options
