# Version Display in GUI — Design

**Date:** 2026-02-24
**Status:** Approved

## Problem

The app version is not visible in the GUI. Users and developers have no way to confirm which version they are running without checking external files.

## Requirements

- Show version number in the sidebar logo area, next to "Budget Analyser"
- Hide version text when the sidebar is collapsed (icon-only mode)
- Version fetches fresh on every app launch or page reload; no mid-session re-fetches
- Version source: FastAPI backend via `importlib.metadata` (reads installed package version)

## Design

### Backend — `api/main.py`

Add a `GET /api/version` endpoint inline alongside the existing `/api/health` endpoint.
Reads the installed package version via `importlib.metadata.version("budget-analyser")`.

```python
@app.get("/api/version")
def version() -> dict[str, str]:
    return {"version": importlib.metadata.version("budget-analyser")}
```

### Frontend — `api/hooks/use-settings.ts`

Add `useAppVersion()` React Query hook following the existing hook pattern.
`staleTime: Infinity` — fetches once on app load/page reload, never re-fetches mid-session.

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

### Frontend — `layouts/app-shell.tsx`

In the logo `div`, add version below the app name, guarded by `!isSidebarCollapsed`:

```
┌─────────────────────────────┐
│  [wallet]  Budget Analyser  │
│            v1.0.3           │  ← text-xs, muted (sidebar-foreground/50)
└─────────────────────────────┘
```

```tsx
{!isSidebarCollapsed && (
  <div className="ml-3 flex flex-col">
    <span className="text-lg font-semibold text-sidebar-foreground">
      Budget Analyser
    </span>
    <span className="text-xs text-sidebar-foreground/50">
      {version ? `v${version}` : ""}
    </span>
  </div>
)}
```

## Data Flow

```
App load / page reload
  → useAppVersion() query mounts (cache empty)
  → GET /api/version
  → importlib.metadata.version("budget-analyser")
  → returns { version: "1.0.3" }
  → displayed as "v1.0.3" in sidebar logo area
```

## Out of Scope

- CI trigger change (AD branch auto-increment) — separate workflow task
- Update check / "new version available" notification
