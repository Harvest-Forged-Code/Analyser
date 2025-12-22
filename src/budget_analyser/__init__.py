"""Budget Analyser application package.

Purpose:
    Provide a structured, layered budget analysis application.

Goal:
    Keep the public package surface small while allowing `python -m budget_analyser`
    to run from the composition root.
"""

from budget_analyser.version import __version__, APP_NAME, get_version

__all__ = ["__version__", "APP_NAME", "get_version"]
