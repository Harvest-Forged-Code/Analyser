# Version Display Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Display the app version (`v1.0.x`) in the sidebar logo area, fetched from a new FastAPI endpoint, hidden when the sidebar is collapsed.

**Architecture:** Add `GET /api/version` to `main.py` (reads installed package version via `importlib.metadata`), add a `useAppVersion()` React Query hook in `use-settings.ts`, and update `app-shell.tsx` to render the version below the app name.

**Tech Stack:** Python `importlib.metadata`, FastAPI, React Query (`@tanstack/react-query`), TypeScript, Tailwind CSS

---

### Task 1: Backend — Add `/api/version` endpoint

**Files:**
- Modify: `src/budget_analyser/api/main.py`
- Test: `src/test/unit/test_api_version.py` (new file)

**Step 1: Write the failing test**

Create `src/test/unit/test_api_version.py`:

```python
from __future__ import annotations

from fastapi.testclient import TestClient

from budget_analyser.api.main import create_app


def test_version_endpoint_returns_version_string() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.get("/api/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest src/test/unit/test_api_version.py -v
```

Expected: FAIL — `404 Not Found` (endpoint doesn't exist yet)

**Step 3: Add the endpoint to `main.py`**

Open `src/budget_analyser/api/main.py`. Add `importlib.metadata` to the imports at the top:

```python
import importlib.metadata
```

Then inside `create_app()`, directly after the existing `/api/health` endpoint block (around line 64), add:

```python
    # ----- version endpoint -----
    @app.get("/api/version")
    def app_version() -> dict[str, str]:
        """Return the installed package version."""
        return {"version": importlib.metadata.version("budget-analyser")}
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest src/test/unit/test_api_version.py -v
```

Expected: PASS

**Step 5: Run full unit suite to confirm no regressions**

```bash
uv run pytest src/test/unit/ -q
```

Expected: all tests pass

**Step 6: Commit**

```bash
git add src/budget_analyser/api/main.py src/test/unit/test_api_version.py
git commit -S -m "feat(api): add GET /api/version endpoint

| Area        | Change                                          |
|-------------|--------------------------------------------------|
| main.py     | Added /api/version endpoint via importlib.metadata |
| test_api_version.py | Added unit test for version endpoint    |

Author: Prabhukumar Sivamorthy"
```

---

### Task 2: Frontend — Add `useAppVersion()` hook

**Files:**
- Modify: `src/frontend/src/api/hooks/use-settings.ts`

No unit test needed — this is a thin React Query wrapper; behaviour is covered by the backend test and manual verification.

**Step 1: Add the hook**

Open `src/frontend/src/api/hooks/use-settings.ts`. Append at the end of the file:

```ts
export function useAppVersion() {
  return useQuery({
    queryKey: ["app", "version"],
    queryFn: async () => {
      const response = await apiClient.get<{ version: string }>("/version");
      return response.data.version;
    },
    staleTime: Infinity,
  });
}
```

Note: The existing hooks import `useQuery` from `@tanstack/react-query` and `apiClient` from `"../client"` — both are already in scope at the top of the file. No new imports needed.

**Step 2: Verify TypeScript compiles**

```bash
cd src/frontend && npx tsc --noEmit
```

Expected: no errors

**Step 3: Commit**

```bash
git add src/frontend/src/api/hooks/use-settings.ts
git commit -S -m "feat(frontend): add useAppVersion React Query hook

| Area              | Change                                        |
|-------------------|-----------------------------------------------|
| use-settings.ts   | Added useAppVersion() with staleTime: Infinity |

Author: Prabhukumar Sivamorthy"
```

---

### Task 3: Frontend — Display version in sidebar logo area

**Files:**
- Modify: `src/frontend/src/layouts/app-shell.tsx`

**Step 1: Import the hook**

Open `src/frontend/src/layouts/app-shell.tsx`. At the top, add `useAppVersion` to the existing import from hooks (or add a new import line after the store imports):

```ts
import { useAppVersion } from "@/api/hooks/use-settings";
```

**Step 2: Call the hook inside `AppShell`**

Inside the `AppShell` function body, after the existing `const { logout } = useAuthStore();` line, add:

```ts
const { data: version } = useAppVersion();
```

**Step 3: Update the logo section**

Find the existing logo `div` block (around line 53–60):

```tsx
<div className="flex h-16 items-center border-b border-sidebar-border px-4">
  <Wallet className="h-6 w-6 text-sidebar-primary" />
  {!isSidebarCollapsed && (
    <span className="ml-3 text-lg font-semibold text-sidebar-foreground">
      Budget Analyser
    </span>
  )}
</div>
```

Replace it with:

```tsx
<div className="flex h-16 items-center border-b border-sidebar-border px-4">
  <Wallet className="h-6 w-6 text-sidebar-primary flex-shrink-0" />
  {!isSidebarCollapsed && (
    <div className="ml-3 flex flex-col min-w-0">
      <span className="text-lg font-semibold text-sidebar-foreground leading-tight">
        Budget Analyser
      </span>
      <span className="text-xs text-sidebar-foreground/50 leading-tight">
        {version ? `v${version}` : ""}
      </span>
    </div>
  )}
</div>
```

**Step 4: Verify TypeScript compiles**

```bash
cd src/frontend && npx tsc --noEmit
```

Expected: no errors

**Step 5: Manual verification**

Start the app:

```bash
cd src/frontend && npm run tauri dev
```

Check:
- [ ] Version appears below "Budget Analyser" in the logo area (e.g., `v1.0.0`)
- [ ] Version is hidden when sidebar is collapsed (click the Collapse button)
- [ ] Version reappears when sidebar is expanded

**Step 6: Commit**

```bash
git add src/frontend/src/layouts/app-shell.tsx
git commit -S -m "feat(ui): display app version in sidebar logo area

| Area           | Change                                              |
|----------------|-----------------------------------------------------|
| app-shell.tsx  | Added version display below app name, hidden on collapse |

Author: Prabhukumar Sivamorthy"
```
