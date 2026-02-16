# ---
# name: api-design
# description: >
#   Use when designing REST or GraphQL APIs -- covers OpenAPI specification,
#   request/response validation, error handling, versioning, authentication,
#   and integration testing. Produces production-grade API code.
# trigger: >
#   When user asks to design, create, plan, or scaffold an API.
#   Keywords: "design API", "create endpoint", "REST API", "GraphQL", "API spec",
#   "add route", "new endpoint", "API versioning".
# inputs:
#   - api_style: enum [REST, GraphQL] (default: REST)
#   - resources: list of resource names and their operations
#   - auth_requirements: description of authentication/authorization needs
# references:
#   - CLAUDE.md [ARCHITECTURE] HLD section for API patterns
#   - CLAUDE.md [PYTHON] section for code style and structure
# ---

# Skill: api-design

## Purpose

Design and implement well-structured, production-grade APIs following REST or GraphQL
conventions. The output includes router definitions, Pydantic schemas, error handling,
authentication dependencies, OpenAPI documentation, and integration tests -- all aligned
with patterns defined in the CLAUDE.md [ARCHITECTURE] HLD section.

---

## Workflow

### Step 1 -- Explore Existing API Patterns

Before writing any code, audit the current codebase to understand conventions already in use.

**Search for:**
- Existing routers: `grep -r "APIRouter\|router\|Blueprint" src/`
- Existing schemas: `grep -r "BaseModel\|BaseSchema" src/`
- Dependency injection patterns: `grep -r "Depends(" src/`
- Error handlers: `grep -r "exception_handler\|HTTPException" src/`
- Middleware: `grep -r "middleware\|Middleware" src/`
- Existing tests: `ls tests/integration/` or `grep -r "TestClient\|AsyncClient" tests/`

**Document findings:**
- Framework in use (FastAPI, Flask, Django REST, Starlette, etc.)
- Schema library (Pydantic v1/v2, Marshmallow, attrs, etc.)
- Authentication pattern (JWT, OAuth2, API key, session)
- Error response format currently used
- URL prefix convention (e.g., `/api/v1/`)
- Pagination pattern (cursor-based, offset-limit, page-number)

If no existing patterns are found, default to FastAPI + Pydantic v2 conventions.

### Step 2 -- Gather Requirements

Collect the following from the user. Do not proceed until confirmed.

| Requirement             | Description                                              | Example                               |
|-------------------------|----------------------------------------------------------|---------------------------------------|
| Resources               | List of domain entities to expose                        | `users`, `orders`, `products`         |
| Operations per resource | CRUD subset or custom actions                            | Users: list, get, create, update      |
| Authentication          | Auth mechanism required                                  | JWT bearer tokens                     |
| Authorization           | Role/permission model                                    | Admin can delete; users read own data |
| Pagination              | Required? What style?                                    | Cursor-based, default page size 20    |
| Filtering/Sorting       | Which fields are filterable/sortable?                    | Filter by status; sort by created_at  |
| Rate limiting           | Required? What limits?                                   | 100 req/min per user                  |
| Versioning strategy     | URL path, header, or query param                         | URL path: `/api/v1/`                  |

### Step 3 -- Design Resource Hierarchy and URL Structure

Map resources to RESTful URL patterns following these conventions:

```
# Collection endpoints
GET    /api/v1/{resource}          -- List (with pagination, filtering)
POST   /api/v1/{resource}          -- Create

# Instance endpoints
GET    /api/v1/{resource}/{id}     -- Retrieve
PUT    /api/v1/{resource}/{id}     -- Full update
PATCH  /api/v1/{resource}/{id}     -- Partial update
DELETE /api/v1/{resource}/{id}     -- Delete

# Nested resources (if parent-child relationship exists)
GET    /api/v1/{parent}/{parent_id}/{child}        -- List children
POST   /api/v1/{parent}/{parent_id}/{child}        -- Create child

# Custom actions (use verbs only when CRUD does not fit)
POST   /api/v1/{resource}/{id}/actions/{action}    -- e.g., /orders/{id}/actions/cancel
```

**Rules:**
- Resource names are plural nouns, lowercase, hyphen-separated for multi-word (`order-items`).
- Never use verbs in URLs except under `/actions/`.
- Nesting depth must not exceed 2 levels.
- All IDs should use UUID format unless the user specifies otherwise.
- Document the full URL map in a table before writing code.

### Step 4 -- Define Pydantic Request/Response Models

Create schemas in `src/{project}/api/schemas/{resource}.py`.

**Naming conventions:**
- `{Resource}Create` -- POST request body
- `{Resource}Update` -- PUT request body (all fields required)
- `{Resource}Patch` -- PATCH request body (all fields optional)
- `{Resource}Response` -- Single resource response
- `{Resource}ListResponse` -- Paginated list response
- `{Resource}Filters` -- Query parameter model for filtering

**Schema design rules:**
```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class ResourceBase(BaseModel):
    """Shared fields between create and response."""
    name: str = Field(..., min_length=1, max_length=255, description="Resource name")
    status: ResourceStatus = Field(default=ResourceStatus.ACTIVE, description="Current status")

class ResourceCreate(ResourceBase):
    """Fields required when creating a resource."""
    pass

class ResourceUpdate(ResourceBase):
    """Fields for full update -- all fields required."""
    pass

class ResourcePatch(BaseModel):
    """Fields for partial update -- all fields optional."""
    name: str | None = Field(None, min_length=1, max_length=255)
    status: ResourceStatus | None = None

class ResourceResponse(ResourceBase):
    """Full resource representation returned to client."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResourceListResponse(BaseModel):
    """Paginated list response."""
    items: list[ResourceResponse]
    total: int
    next_cursor: str | None = None
    has_more: bool
```

**Validation rules to include:**
- String fields: `min_length`, `max_length` constraints.
- Numeric fields: `ge`, `le`, `gt`, `lt` constraints where applicable.
- Email fields: use `EmailStr` from pydantic.
- All enums: define as `StrEnum` classes.
- Nested objects: define as separate schema classes, never as raw dicts.

### Step 5 -- Design Error Response Format

Create a consistent error format used across all endpoints.

**Error schema:**
```python
class ErrorDetail(BaseModel):
    """Individual error detail."""
    field: str | None = None
    message: str
    code: str

class ErrorResponse(BaseModel):
    """Standard error response body."""
    error: str           # Machine-readable error code: "VALIDATION_ERROR", "NOT_FOUND"
    message: str         # Human-readable description
    details: list[ErrorDetail] = []
    request_id: str      # Correlation ID for debugging
```

**Standard error codes and their HTTP status mappings:**

| Error Code             | HTTP Status | When to Use                            |
|------------------------|-------------|----------------------------------------|
| `VALIDATION_ERROR`     | 422         | Request body/params fail validation    |
| `NOT_FOUND`            | 404         | Resource does not exist                |
| `ALREADY_EXISTS`       | 409         | Unique constraint violation            |
| `UNAUTHORIZED`         | 401         | Missing or invalid credentials         |
| `FORBIDDEN`            | 403         | Valid credentials, insufficient perms  |
| `RATE_LIMITED`         | 429         | Too many requests                      |
| `INTERNAL_ERROR`       | 500         | Unhandled server error                 |
| `SERVICE_UNAVAILABLE`  | 503         | Downstream dependency failure          |

**Implement exception handlers:**
```python
# Register global exception handlers on the FastAPI app
@app.exception_handler(ResourceNotFoundError)
async def not_found_handler(request: Request, exc: ResourceNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="NOT_FOUND",
            message=str(exc),
            request_id=request.state.request_id,
        ).model_dump(),
    )
```

### Step 6 -- Create Router with Endpoint Stubs

Create router in `src/{project}/api/routers/{resource}.py`.

**Structure:**
```python
from fastapi import APIRouter, Depends, Query, Path, status
from uuid import UUID

router = APIRouter(prefix="/{resource}", tags=["{Resource}"])

@router.get(
    "",
    response_model=ResourceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List {resources}",
    description="Retrieve a paginated list of {resources} with optional filtering.",
)
async def list_resources(
    filters: ResourceFilters = Depends(),
    cursor: str | None = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    service: ResourceService = Depends(get_resource_service),
) -> ResourceListResponse:
    ...

@router.post(
    "",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create {resource}",
)
async def create_resource(
    body: ResourceCreate,
    service: ResourceService = Depends(get_resource_service),
) -> ResourceResponse:
    ...

@router.get(
    "/{resource_id}",
    response_model=ResourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get {resource}",
)
async def get_resource(
    resource_id: UUID = Path(..., description="{Resource} ID"),
    service: ResourceService = Depends(get_resource_service),
) -> ResourceResponse:
    ...

@router.put(
    "/{resource_id}",
    response_model=ResourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update {resource}",
)
async def update_resource(
    resource_id: UUID = Path(..., description="{Resource} ID"),
    body: ResourceUpdate,
    service: ResourceService = Depends(get_resource_service),
) -> ResourceResponse:
    ...

@router.patch(
    "/{resource_id}",
    response_model=ResourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update {resource}",
)
async def patch_resource(
    resource_id: UUID = Path(..., description="{Resource} ID"),
    body: ResourcePatch,
    service: ResourceService = Depends(get_resource_service),
) -> ResourceResponse:
    ...

@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete {resource}",
)
async def delete_resource(
    resource_id: UUID = Path(..., description="{Resource} ID"),
    service: ResourceService = Depends(get_resource_service),
) -> None:
    ...
```

**HTTP method and status code rules:**
- `GET` returns `200`.
- `POST` (create) returns `201`.
- `PUT`/`PATCH` returns `200`.
- `DELETE` returns `204` with no body.
- Never return `200` for a creation operation.

### Step 7 -- Add Authentication and Authorization Dependencies

Create dependencies in `src/{project}/api/dependencies/auth.py`.

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Validate JWT token and return current user."""
    token = credentials.credentials
    try:
        payload = decode_jwt(token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
    user = await user_service.get_by_id(payload.sub)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user

def require_role(*roles: str):
    """Factory for role-based authorization dependency."""
    async def _check_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user
    return _check_role
```

**Apply to endpoints:**
- Public endpoints: no auth dependency.
- Authenticated endpoints: `current_user: User = Depends(get_current_user)`.
- Admin-only endpoints: `current_user: User = Depends(require_role("admin"))`.

### Step 8 -- Write OpenAPI Docstrings

Every endpoint must have:
1. A `summary` (short, imperative verb phrase): "List orders", "Create user".
2. A `description` (full sentence explaining behavior, edge cases, permissions).
3. `response_model` with accurate type.
4. Documented query parameters with `description` on each `Query()`.
5. Documented path parameters with `description` on each `Path()`.
6. Response descriptions for non-200 status codes:

```python
@router.get(
    "/{resource_id}",
    response_model=ResourceResponse,
    summary="Get resource by ID",
    description="Retrieve a single resource by its UUID. Returns 404 if not found.",
    responses={
        404: {"model": ErrorResponse, "description": "Resource not found"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
    },
)
```

Tag grouping: each router must have a `tags` parameter for logical grouping in the docs.

### Step 9 -- Create Integration Tests

Create test file `tests/integration/test_{resource}_api.py`.

**Test structure:**
```python
import pytest
from httpx import AsyncClient
from uuid import uuid4

pytestmark = pytest.mark.asyncio

class TestList{Resource}:
    async def test_list_returns_200(self, async_client: AsyncClient, auth_headers: dict):
        response = await async_client.get("/api/v1/{resource}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_list_pagination(self, async_client: AsyncClient, auth_headers: dict):
        response = await async_client.get(
            "/api/v1/{resource}?limit=5", headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) <= 5

    async def test_list_unauthenticated_returns_401(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/{resource}")
        assert response.status_code == 401

class TestCreate{Resource}:
    async def test_create_valid_returns_201(self, async_client: AsyncClient, auth_headers: dict):
        payload = {"name": "Test Resource", "status": "active"}
        response = await async_client.post(
            "/api/v1/{resource}", json=payload, headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Resource"
        assert "id" in data

    async def test_create_invalid_returns_422(self, async_client: AsyncClient, auth_headers: dict):
        payload = {"name": ""}  # Violates min_length
        response = await async_client.post(
            "/api/v1/{resource}", json=payload, headers=auth_headers
        )
        assert response.status_code == 422

class TestGet{Resource}:
    async def test_get_existing_returns_200(self, async_client, auth_headers, created_resource):
        response = await async_client.get(
            f"/api/v1/{resource}/{created_resource.id}", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_get_nonexistent_returns_404(self, async_client, auth_headers):
        response = await async_client.get(
            f"/api/v1/{resource}/{uuid4()}", headers=auth_headers
        )
        assert response.status_code == 404

class TestUpdate{Resource}:
    async def test_full_update_returns_200(self, async_client, auth_headers, created_resource):
        payload = {"name": "Updated Name", "status": "active"}
        response = await async_client.put(
            f"/api/v1/{resource}/{created_resource.id}",
            json=payload, headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    async def test_partial_update_returns_200(self, async_client, auth_headers, created_resource):
        payload = {"name": "Patched Name"}
        response = await async_client.patch(
            f"/api/v1/{resource}/{created_resource.id}",
            json=payload, headers=auth_headers,
        )
        assert response.status_code == 200

class TestDelete{Resource}:
    async def test_delete_returns_204(self, async_client, auth_headers, created_resource):
        response = await async_client.delete(
            f"/api/v1/{resource}/{created_resource.id}", headers=auth_headers
        )
        assert response.status_code == 204

    async def test_delete_nonexistent_returns_404(self, async_client, auth_headers):
        response = await async_client.delete(
            f"/api/v1/{resource}/{uuid4()}", headers=auth_headers
        )
        assert response.status_code == 404
```

**Minimum test coverage per endpoint:**
- Happy path (valid request, expected response).
- Validation error (invalid input, expect 422).
- Not found (nonexistent ID, expect 404).
- Unauthorized (no auth, expect 401).
- Forbidden (wrong role, expect 403) -- if roles are used.

### Step 10 -- Verify

Run the following checks and fix any issues before completing:

```bash
# 1. Lint all new files
ruff check src/{project}/api/ tests/integration/

# 2. Type check
mypy src/{project}/api/

# 3. Run integration tests
pytest tests/integration/test_{resource}_api.py -v

# 4. Verify OpenAPI docs render
# Start the dev server and confirm /docs or /redoc loads without errors
uvicorn {project}.main:app --host 0.0.0.0 --port 8000
# Check: http://localhost:8000/docs
# Check: http://localhost:8000/openapi.json

# 5. Verify error responses match expected format
pytest tests/integration/ -k "error or invalid or 4"
```

All checks must pass. Fix any issues before declaring the task complete.

---

## Enforced Standards

### Google-Style Docstrings (MANDATORY)
Every function, method, and class written or modified during API design MUST have a Google-style docstring. No exceptions. This includes:
- One-line summary in imperative mood
- Args section for all parameters
- Returns section describing what is returned
- Raises section for all exceptions
- See CLAUDE.md [STANDARDS] for full specification and examples.

### Git Commit Format (MANDATORY)
All commits created during API design MUST follow this format:
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

- [ ] Existing codebase patterns explored and documented
- [ ] All resources and operations confirmed with user
- [ ] URL structure follows REST conventions (plural nouns, no verbs)
- [ ] Pydantic schemas created for Create, Update, Patch, Response, List, Filters
- [ ] All schema fields have validation constraints and descriptions
- [ ] Error response format is consistent across all endpoints
- [ ] All standard error codes mapped to HTTP status codes
- [ ] Router created with correct HTTP methods and status codes
- [ ] Authentication dependency applied to protected endpoints
- [ ] Authorization (role check) applied where needed
- [ ] Every endpoint has summary, description, and response docs
- [ ] Non-200 responses documented in OpenAPI responses dict
- [ ] Integration tests cover happy path, validation, 404, 401, 403
- [ ] `ruff check` passes on all new files
- [ ] `mypy` passes on all new files
- [ ] `pytest` passes all new tests
- [ ] OpenAPI docs render correctly at /docs
- [ ] No hardcoded secrets or credentials in any file
