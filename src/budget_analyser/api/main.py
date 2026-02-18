"""FastAPI application entry point for Budget Analyser API.

Provides the app factory and uvicorn runner for the REST API
that wraps existing feature controllers.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from budget_analyser.api import dependencies
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
)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialise shared controllers on startup."""
    dependencies.initialize()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully-configured FastAPI instance with CORS and all routers.
    """
    app = FastAPI(
        title="Budget Analyser API",
        version="0.1.0",
        lifespan=_lifespan,
    )

    # CORS - allow all origins for the desktop Tauri shell
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ----- health endpoint -----
    @app.get("/api/health")
    def health() -> dict[str, str]:
        """Return a simple health-check response."""
        return {"status": "healthy"}

    # ----- register all routers -----
    app.include_router(auth.router)
    app.include_router(reports.router)
    app.include_router(dashboard.router)
    app.include_router(earnings.router)
    app.include_router(expenses.router)
    app.include_router(budget_goals.router)
    app.include_router(savings.router)
    app.include_router(mappers.router)
    app.include_router(upload.router)
    app.include_router(settings.router)
    app.include_router(recategorize.router)

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "budget_analyser.api.main:app",
        host="127.0.0.1",
        port=8741,
        reload=False,
    )
