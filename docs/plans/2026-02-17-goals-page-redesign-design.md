# Goals Page Redesign - Design Document

**Date:** 2026-02-17
**Status:** Approved
**Approach:** Enhanced Card Dashboard (Approach 1)

## Overview

Full redesign of the Budget Goals page covering visuals, UX, and new features. Transform from plain tables to a rich dashboard-card UI (Mint/YNAB style) while keeping the 3-tab structure.

### Key Decisions

- **Visual style:** Dashboard cards with icons, gauges, and visual indicators
- **Goal management:** Set once (ALL), override per month as needed
- **Tab structure:** Keep 3 tabs (Budget Goals, Earnings Goals, Progress)
- **Progress view:** Monthly overview + category drill-down with historical charts
- **Backend:** Additive endpoints only, no schema changes

## Tab 1: Budget Goals

### Summary Strip

Horizontal strip of 3 stat cards at the top:

| Card | Value | Source |
|------|-------|--------|
| Total Monthly Budget | Sum of all active goals | `GET /api/budget-goals/summary` |
| Categories Tracked | Count of categories with goals | Same endpoint |
| Month Overrides | Count of month-specific overrides | Same endpoint |

### Goal Cards Grid

Responsive card grid (3 cols desktop, 2 tablet, 1 mobile). Replaces the current table.

Each **Budget Goal Card** contains:
- Category name (header, bold)
- Monthly limit displayed prominently (e.g., "$350/mo")
- Year/month scope badge: "All Months" or specific month
- Override indicator: badge like "2 overrides" that expands on click
- Edit button (pencil icon) opens edit dialog
- Delete button (trash icon) with confirmation

### Add Goal Dialog

Triggered by "+ Add Budget Goal" button (top-right):
- Category dropdown (populated from mapper categories)
- Monthly limit number input
- Scope selector: "All months" toggle vs. specific month picker

### Empty State

Centered icon with "No budget goals yet. Set your first spending limit to start tracking." and CTA button.

## Tab 2: Earnings Goals

Symmetric with Budget Goals tab, with earnings-specific terminology.

### Summary Strip

| Card | Value |
|------|-------|
| Total Expected Earnings | Sum of all earnings goals |
| Sub-categories Tracked | Count of sub-categories with goals |
| Month Overrides | Count of month-specific overrides |

### Earnings Goal Cards Grid

Same responsive grid. Each card shows:
- Sub-category name (header)
- Expected amount (e.g., "$2,000/mo")
- Scope badge and override indicator
- Edit/Delete buttons

### Add Earnings Goal Dialog

- Sub-category dropdown (from earnings sub-categories)
- Expected amount number input
- Scope selector: "All months" vs. specific month picker

## Tab 3: Progress

The most visually rich tab -- tracking and insights.

### Top Controls

- Month selector dropdown (populated from available months)
- View toggle: "Overview" | "Detail" (segmented control)

### Overview Mode (default)

**Summary Cards Row (4 cards):**

| Card | Description | Color |
|------|-------------|-------|
| On Track | Categories under 75% | Green |
| Warning | Categories 75-100% | Yellow/Amber |
| Over Budget | Categories exceeding 100% | Red |
| Total Spent | Aggregate spend vs budget | Neutral |

**Progress Cards Grid (3 columns):**

Each card per category:
- Category name + status badge (color-coded)
- Circular progress gauge (Recharts RadialBarChart)
- "Spent / Budget" text (e.g., "$280 / $350")
- Remaining amount (green if positive, red if negative)
- Click to drill down into Detail mode

Cards sorted by percentage descending (most urgent first).

### Detail Mode (drill-down)

Activated by clicking a category card:
- Back button to return to Overview
- Category header with current month status
- **Line chart** (Recharts LineChart) showing spend vs budget over last 12 months:
  - Blue line: actual spend
  - Dashed gray line: budget limit
  - Red fill area where spend exceeds budget
- **Monthly breakdown table**: Month, Budget, Spent, Remaining, Status columns
- **Override management**: Inline editing of month-specific overrides

## Backend Changes

### New Endpoints (Additive)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/budget-goals/summary` | Summary stats for Budget Goals tab strip |
| `GET` | `/api/earnings-goals/summary` | Summary stats for Earnings Goals tab strip |
| `GET` | `/api/budget-goals/progress/history/{category}` | 12-month progress history for drill-down chart |
| `GET` | `/api/budget-goals/progress/{year_month}/summary` | Aggregate progress summary for a month |

### New Service Function

`calculate_category_progress_history(category, months=12)` in `service.py` -- computes historical progress for the drill-down chart.

### No Changes Required

- All existing CRUD endpoints remain unchanged
- No database schema changes needed
- Existing `budget_goals` and `earnings_goals` tables are sufficient

## Tech Stack

- **UI Components:** Radix UI primitives (Dialog, Tabs, Select, Progress)
- **Styling:** Tailwind CSS v4
- **Charts:** Recharts (RadialBarChart for gauges, LineChart for trends)
- **Icons:** Lucide React
- **Data fetching:** React Query (TanStack Query)
- **State:** Local component state + React Query cache

## Data Flow

```
Frontend (React)
  |-- Budget/Earnings tabs --> CRUD hooks --> existing endpoints
  |-- Summary strips --> new summary endpoints
  |-- Progress Overview --> existing progress endpoint + new summary endpoint
  |-- Progress Detail --> new history endpoint
  |
API Layer (FastAPI routers)
  |-- budget_goals.py (existing + 4 new endpoints)
  |
Controller (BudgetGoalsController)
  |-- existing methods + calculate_category_progress_history()
  |
Service (service.py)
  |-- existing functions + calculate_category_progress_history()
  |
Repository (repository.py)
  |-- No changes needed
  |
Database (SQLite)
  |-- budget_goals, earnings_goals tables (unchanged)
```
