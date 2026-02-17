"""FastAPI routers for Budget Analyser API.

This package contains all REST API route definitions organized by
feature domain. Each router module handles a specific area of
functionality (auth, reports, earnings, expenses, etc.).
"""

from __future__ import annotations

__all__ = [
    "auth",
    "reports",
    "dashboard",
    "earnings",
    "expenses",
    "budget_goals",
    "net_worth",
    "recurring",
    "savings",
    "payments",
    "forecasting",
    "trends",
    "mappers",
    "upload",
    "export",
    "settings",
]
