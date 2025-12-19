"""Application composition root.

Default behavior:
    Launch the PySide6 GUI application (fullscreen login -> dashboard).
"""

from __future__ import annotations

from budget_analyser.views.app_gui import run_app as run_gui


def main() -> None:
    """Run the PySide6 GUI application by default."""
    run_gui()


if __name__ == "__main__":
    main()
