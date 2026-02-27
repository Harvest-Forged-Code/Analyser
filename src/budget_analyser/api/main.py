"""FastAPI application entry point for Budget Analyser API.

Provides the app factory and uvicorn runner for the REST API
that wraps existing feature controllers.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from budget_analyser.api import dependencies
from budget_analyser.version import get_version
from budget_analyser.settings.seeding import seed_data_directory
from budget_analyser.api.routers import (
    auth,
    reports,
    dashboard,
    earnings,
    expenses,
    budget_goals,
    savings,
    mappers,
    upload,
    settings,
    recategorize,
    updates,
)


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Seed data directory then initialise shared controllers on startup."""
    data_dir_env = os.environ.get("BUDGET_ANALYSER_DATA_DIR", "")
    if data_dir_env:
        seed_data_directory(Path(data_dir_env))
    dependencies.initialize()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully-configured FastAPI instance with CORS and all routers.
    """
    fastapi_app = FastAPI(
        title="Budget Analyser API",
        version="0.1.0",
        lifespan=_lifespan,
    )

    # CORS - allow all origins for the desktop Tauri shell
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ----- health endpoint -----
    @fastapi_app.get("/api/health")
    def health() -> dict[str, str]:
        """Return a simple health-check response."""
        return {"status": "healthy"}

    # ----- version endpoint -----
    @fastapi_app.get("/api/version")
    def app_version() -> dict[str, str]:
        """Return the installed package version."""
        return {"version": get_version()}

    # ----- register all routers -----
    fastapi_app.include_router(auth.router)
    fastapi_app.include_router(reports.router)
    fastapi_app.include_router(dashboard.router)
    fastapi_app.include_router(earnings.router)
    fastapi_app.include_router(expenses.router)
    fastapi_app.include_router(budget_goals.router)
    fastapi_app.include_router(savings.router)
    fastapi_app.include_router(mappers.router)
    fastapi_app.include_router(upload.router)
    fastapi_app.include_router(settings.router)
    fastapi_app.include_router(recategorize.router)
    fastapi_app.include_router(updates.router)

    return fastapi_app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8741,
        reload=False,
    )
