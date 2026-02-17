"""Application entry point.

Launches the FastAPI server via uvicorn on port 8741.
"""

from __future__ import annotations

import uvicorn


def main() -> None:
    """Run the FastAPI application via uvicorn."""
    uvicorn.run(
        "budget_analyser.api.main:app",
        host="127.0.0.1",
        port=8741,
        reload=False,
    )


if __name__ == "__main__":
    main()
