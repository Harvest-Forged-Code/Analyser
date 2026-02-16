# ---
# name: database-design
# description: >
#   Use when designing database schemas, migrations, indexes, or data access layers.
#   Covers SQLAlchemy model definition, Alembic migrations, repository pattern,
#   indexing strategy, and constraint enforcement.
# trigger: >
#   When user asks to design a schema, add tables, create migrations, model data,
#   or build a data access layer.
#   Keywords: "database", "schema", "migration", "table", "model", "repository",
#   "index", "foreign key", "ORM", "SQLAlchemy", "Alembic".
# inputs:
#   - entities: list of entity names and their attributes
#   - relationships: how entities relate to each other
#   - query_patterns: expected read/write patterns and access paths
# references:
#   - CLAUDE.md [ARCHITECTURE] database design principles
#   - CLAUDE.md [PYTHON] section for code style
# ---

# Skill: database-design

## Purpose

Design and implement robust database schemas with proper normalization, indexing,
constraints, migration management, and data access layers. All designs follow the
database principles defined in CLAUDE.md [ARCHITECTURE] and produce production-ready
SQLAlchemy models with Alembic migrations.

---

## Workflow

### Step 1 -- Explore Existing Models, Migrations, and Data Access Patterns

Audit the current codebase before making any changes.

**Search for:**
- Existing SQLAlchemy models: `grep -r "DeclarativeBase\|declarative_base\|Base\|mapped_column" src/`
- Existing Alembic configuration: `ls alembic/ alembic.ini` or `ls migrations/`
- Repository or DAO patterns: `grep -r "Repository\|repository\|DAO" src/`
- Session management: `grep -r "AsyncSession\|sessionmaker\|get_session\|get_db" src/`
- Existing migrations: `ls alembic/versions/` or `ls migrations/versions/`
- Naming conventions in existing models (table names, column names, constraint names)

**Document findings:**
- Database engine (PostgreSQL, MySQL, SQLite, etc.)
- SQLAlchemy version and style (1.4 legacy vs 2.0 mapped_column)
- Async or sync session usage
- Base class location and import path
- Naming conventions: table names (plural/singular), column style (snake_case)
- Existing relationships and how they are modeled
- Migration naming convention

If no existing patterns are found, default to:
- SQLAlchemy 2.0 with `mapped_column` and type annotations
- Async sessions with `asyncpg`
- PostgreSQL as the target database
- Repository pattern for data access

### Step 2 -- Gather Requirements

Collect the following from the user. Do not proceed without confirmation.

| Requirement       | Description                                          | Example                                    |
|-------------------|------------------------------------------------------|--------------------------------------------|
| Entities          | Domain objects to persist                            | User, Order, Product, OrderItem            |
| Attributes        | Fields per entity with types                         | User: name (str), email (str), active (bool)|
| Relationships     | How entities relate                                  | User has many Orders; Order has many Items  |
| Query patterns    | Most frequent read operations                        | "Get user by email", "List orders by date" |
| Write patterns    | Most frequent write operations                       | "Create order with items", "Bulk insert"   |
| Soft delete       | Required for any entity?                             | Yes for User, no for OrderItem             |
| Audit fields      | created_at, updated_at, created_by needed?           | Yes, all entities                          |
| Multi-tenancy     | Tenant isolation required?                           | Yes, tenant_id on all tables               |

### Step 3 -- Design Normalized Schema

Design the schema to at least Third Normal Form (3NF).

**Normalization checklist:**
1. **1NF**: Every column holds atomic values. No repeating groups or arrays for structured data.
2. **2NF**: Every non-key column depends on the entire primary key (relevant for composite keys).
3. **3NF**: No transitive dependencies -- non-key columns depend only on the primary key.

**When to denormalize (document justification):**
- Read-heavy query that would require 3+ joins -- add computed/cached column.
- Reporting tables -- create materialized views or summary tables.
- Never denormalize without measuring the query performance impact first.

**Produce an entity-relationship diagram in text form:**
```
[User] 1---* [Order] 1---* [OrderItem] *---1 [Product]
  |                                             |
  +--has_many-----------------------------------+
                   (via OrderItem)
```

**Document each table:**
```
Table: users
-----------------------------------------
Column        | Type         | Constraints
-----------------------------------------
id            | UUID         | PK, default=uuid4
email         | VARCHAR(255) | UNIQUE, NOT NULL
name          | VARCHAR(255) | NOT NULL
password_hash | VARCHAR(255) | NOT NULL
is_active     | BOOLEAN      | NOT NULL, default=true
created_at    | TIMESTAMPTZ  | NOT NULL, default=now()
updated_at    | TIMESTAMPTZ  | NOT NULL, default=now(), onupdate=now()
-----------------------------------------
Indexes: ix_users_email (UNIQUE)
```

### Step 4 -- Define SQLAlchemy Models

Create models in `src/{project}/models/{entity}.py`.

**Use SQLAlchemy 2.0 style with full type annotations:**

```python
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from {project}.models.base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from {project}.models.order import Order


class User(TimestampMixin, SoftDeleteMixin, Base):
    """User account model."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_email", "email"),
        Index("ix_users_is_active", "is_active", postgresql_where=text("is_active = true")),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    orders: Mapped[list[Order]] = relationship(
        back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r})>"
```

**Base model with mixins:**

```python
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Declarative base for all models."""
    pass

class TimestampMixin:
    """Adds created_at and updated_at columns."""
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False
    )

class SoftDeleteMixin:
    """Adds soft delete support via deleted_at column."""
    deleted_at: Mapped[datetime | None] = mapped_column(default=None, nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
```

**Model design rules:**
- Every table gets a UUID primary key unless the user specifies otherwise.
- Use `Mapped[]` type annotations on every column.
- Use `mapped_column()` instead of `Column()`.
- Relationships use `TYPE_CHECKING` imports to avoid circular dependencies.
- `__repr__` on every model for debugging.
- `__table_args__` for composite indexes, constraints, and table-level config.
- All string columns must have explicit length limits.
- No nullable columns unless there is a documented reason.

### Step 5 -- Add Indexes Based on Query Patterns

For each query pattern identified in Step 2, define an appropriate index.

**Index selection guide:**

| Query Pattern                        | Index Type                          |
|--------------------------------------|-------------------------------------|
| Lookup by single column              | B-tree index on that column         |
| Lookup by multiple columns together  | Composite B-tree index              |
| Text search / LIKE queries           | GIN index with pg_trgm extension    |
| Range queries (date ranges)          | B-tree index on the date column     |
| JSON field queries                   | GIN index on the JSON column        |
| Filtered queries (WHERE active=true) | Partial index with `postgresql_where` |
| Unique constraint                    | Unique index                        |
| Foreign key column                   | B-tree index (auto in some DBs)     |

**Rules:**
- Every foreign key column must have an index.
- Columns used in WHERE clauses of frequent queries must have indexes.
- Columns used in ORDER BY of frequent queries should have indexes.
- Composite indexes: put the most selective column first.
- Do not over-index -- each index has write overhead. Justify each index.
- Name all indexes explicitly: `ix_{table}_{column}` or `ix_{table}_{col1}_{col2}`.

### Step 6 -- Create Alembic Migration

Generate and refine the migration.

**Steps:**
```bash
# 1. Auto-generate migration from model changes
alembic revision --autogenerate -m "add_{table_name}_table"

# 2. Review the generated migration file
# 3. Edit if needed: add data migrations, fix index names, add comments
```

**Migration file requirements:**
- `upgrade()` creates tables, indexes, constraints in dependency order.
- `downgrade()` drops in reverse dependency order.
- Data migrations (if any) are in separate migration files from schema changes.
- All constraint and index names are explicit (never auto-generated).
- Migration includes comments explaining non-obvious decisions.

**Migration template:**
```python
"""Add users table.

Revision ID: abc123
Revises: previous_rev
Create Date: 2025-01-15 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "abc123"
down_revision = "previous_rev"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index(
        "ix_users_is_active", "users", ["is_active"],
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_users_is_active", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
```

### Step 7 -- Design Repository Layer

Create repository in `src/{project}/repositories/{entity}.py`.

**Repository pattern with async support:**

```python
from __future__ import annotations

from uuid import UUID
from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from {project}.models.user import User


class UserRepository:
    """Data access layer for User entity."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Fetch a single user by primary key."""
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a single user by email address."""
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> tuple[Sequence[User], int]:
        """List users with pagination and optional filtering. Returns (items, total)."""
        stmt = select(User).where(User.deleted_at.is_(None))
        count_stmt = select(func.count()).select_from(User).where(User.deleted_at.is_(None))

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
            count_stmt = count_stmt.where(User.is_active == is_active)

        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.offset(offset).limit(limit).order_by(User.created_at.desc())
        result = await self._session.execute(stmt)
        return result.scalars().all(), total

    async def create(self, user: User) -> User:
        """Persist a new user to the database."""
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """Update an existing user (assumes already in session)."""
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def soft_delete(self, user: User) -> None:
        """Mark a user as deleted without removing the row."""
        from datetime import datetime, timezone
        user.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
```

**Repository design rules:**
- One repository class per aggregate root entity.
- Repository accepts `AsyncSession` in constructor (dependency injection).
- All queries filter out soft-deleted records by default.
- Return types are explicit: `Entity | None` for single, `Sequence[Entity]` for lists.
- List methods return `tuple[Sequence[Entity], int]` (items + total count).
- No business logic in the repository -- only data access.
- Use `flush()` instead of `commit()` -- let the service layer manage transactions.

### Step 8 -- Add Constraints

Ensure all integrity constraints are explicitly defined.

**Constraint types to consider:**

| Constraint Type   | When to Use                                        | SQLAlchemy Syntax                     |
|-------------------|----------------------------------------------------|---------------------------------------|
| PRIMARY KEY       | Every table must have one                          | `primary_key=True`                    |
| UNIQUE            | Natural keys, email, username, slug                | `UniqueConstraint("col", name="uq_")` |
| NOT NULL          | All columns unless explicitly optional             | `nullable=False`                      |
| FOREIGN KEY       | Every relationship reference                       | `ForeignKey("table.col")`             |
| CHECK             | Value ranges, enum validation at DB level          | `CheckConstraint("col > 0")`         |
| DEFAULT           | Timestamps, boolean flags, status fields           | `server_default=sa.true()`           |
| CASCADE           | Deletion behavior for parent-child relationships   | `ondelete="CASCADE"`                 |
| RESTRICT          | Prevent deletion if children exist                 | `ondelete="RESTRICT"`                |

**Rules:**
- Name all constraints explicitly: `uq_{table}_{columns}`, `ck_{table}_{rule}`, `fk_{table}_{ref_table}`.
- Foreign keys: always specify `ondelete` behavior (`CASCADE`, `SET NULL`, or `RESTRICT`).
- Check constraints for enum-like columns: validate at the DB level, not just the app level.
- Default values: use `server_default` for database-level defaults (not Python-level `default`).

### Step 9 -- Write Unit Tests

Create tests in `tests/unit/test_models_{entity}.py` and `tests/unit/test_repo_{entity}.py`.

**Model tests:**
```python
import pytest
from uuid import uuid4
from {project}.models.user import User


class TestUserModel:
    def test_create_user_with_required_fields(self):
        user = User(
            id=uuid4(),
            email="test@example.com",
            name="Test User",
            password_hash="hashed_value",
        )
        assert user.email == "test@example.com"
        assert user.is_active is True  # default

    def test_soft_delete_marks_deleted(self):
        user = User(id=uuid4(), email="t@t.com", name="T", password_hash="h")
        assert user.is_deleted is False
        from datetime import datetime, timezone
        user.deleted_at = datetime.now(timezone.utc)
        assert user.is_deleted is True

    def test_repr(self):
        user = User(id=uuid4(), email="repr@test.com", name="R", password_hash="h")
        assert "repr@test.com" in repr(user)
```

**Repository tests (using async test database session):**
```python
import pytest
from uuid import uuid4

pytestmark = pytest.mark.asyncio


class TestUserRepository:
    async def test_create_and_get_by_id(self, user_repo, sample_user):
        created = await user_repo.create(sample_user)
        assert created.id is not None
        fetched = await user_repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.email == sample_user.email

    async def test_get_by_email(self, user_repo, sample_user):
        await user_repo.create(sample_user)
        fetched = await user_repo.get_by_email(sample_user.email)
        assert fetched is not None

    async def test_get_by_email_not_found(self, user_repo):
        fetched = await user_repo.get_by_email("nonexistent@test.com")
        assert fetched is None

    async def test_list_with_pagination(self, user_repo, many_users):
        items, total = await user_repo.list(offset=0, limit=5)
        assert len(items) == 5
        assert total == len(many_users)

    async def test_list_filter_active(self, user_repo, active_user, inactive_user):
        items, total = await user_repo.list(is_active=True)
        assert all(u.is_active for u in items)

    async def test_soft_delete(self, user_repo, sample_user):
        created = await user_repo.create(sample_user)
        await user_repo.soft_delete(created)
        fetched = await user_repo.get_by_id(created.id)
        assert fetched.is_deleted is True

    async def test_soft_deleted_excluded_from_list(self, user_repo, sample_user):
        created = await user_repo.create(sample_user)
        await user_repo.soft_delete(created)
        items, total = await user_repo.list()
        assert created.id not in [u.id for u in items]

    async def test_get_nonexistent_returns_none(self, user_repo):
        fetched = await user_repo.get_by_id(uuid4())
        assert fetched is None
```

### Step 10 -- Verify

Run all verification steps and resolve any failures.

```bash
# 1. Run migration up
alembic upgrade head

# 2. Verify tables exist
# Connect to DB and check: \dt (psql) or SELECT * FROM information_schema.tables

# 3. Run migration down
alembic downgrade -1

# 4. Run migration up again (proves reversibility)
alembic upgrade head

# 5. Run model and repository unit tests
pytest tests/unit/test_models_*.py tests/unit/test_repo_*.py -v

# 6. Lint new code
ruff check src/{project}/models/ src/{project}/repositories/

# 7. Type check
mypy src/{project}/models/ src/{project}/repositories/

# 8. Check for missing indexes on foreign keys
# Review all ForeignKey columns and confirm each has an index
```

All steps must pass. Fix issues before declaring the task complete.

---

## Enforced Standards

### Google-Style Docstrings (MANDATORY)
Every function, method, and class written or modified during database design MUST have a Google-style docstring. No exceptions. This includes:
- One-line summary in imperative mood
- Args section for all parameters
- Returns section describing what is returned
- Raises section for all exceptions
- See CLAUDE.md [STANDARDS] for full specification and examples.

### Git Commit Format (MANDATORY)
All commits created during database design MUST follow this format:
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

- [ ] Existing models, migrations, and patterns explored
- [ ] All entities, attributes, and relationships confirmed with user
- [ ] Schema is normalized to at least 3NF
- [ ] All denormalization decisions documented with justification
- [ ] SQLAlchemy models use 2.0 style with `Mapped[]` and `mapped_column()`
- [ ] `TimestampMixin` applied to all models (created_at, updated_at)
- [ ] `SoftDeleteMixin` applied where required
- [ ] All string columns have explicit length limits
- [ ] No nullable columns without documented justification
- [ ] Every foreign key column has an index
- [ ] Indexes added for all frequent query patterns
- [ ] Partial indexes used where filtering is common
- [ ] All indexes and constraints have explicit names
- [ ] Alembic migration created with clean `upgrade()` and `downgrade()`
- [ ] Migration tested: up, down, up cycle works
- [ ] Repository layer implements async CRUD operations
- [ ] Repositories filter soft-deleted records by default
- [ ] Repositories use `flush()` not `commit()`
- [ ] All constraints defined: PK, FK, UNIQUE, CHECK, NOT NULL
- [ ] Foreign keys have explicit `ondelete` behavior
- [ ] Unit tests cover model creation, defaults, and repr
- [ ] Repository tests cover CRUD, pagination, filtering, edge cases
- [ ] `ruff check` passes on all new files
- [ ] `mypy` passes on all new files
- [ ] `pytest` passes all new tests
