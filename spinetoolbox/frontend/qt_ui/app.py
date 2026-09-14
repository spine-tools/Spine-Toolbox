"""Launcher for the Qt frontend UI.
Provides `start_qt_ui` to be called from a shared backend.
"""
from typing import Optional, Tuple
import sys

try:
    from PySide6.QtWidgets import QApplication
except Exception as e:  # pragma: no cover - runtime environment
    raise

from .ui_main_window import MainWindow
from .fluent_integration import init_fluent_for_app


def start_qt_ui(app: Optional[QApplication] = None, exec_loop: bool = False) -> Tuple[MainWindow, Optional[int]]:
    """Start the Qt UI and return the MainWindow.

    Args:
        app: optional QApplication; if None one will be created.
        exec_loop: if True, call `app.exec()` and return its exit code.

    Returns:
        (main_window, exit_code_or_None)
    """
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True

    # Try to initialize Fluent theme if available
    try:
        init_fluent_for_app(app, theme="dark")
    except Exception:
        pass

    window = MainWindow()
    window.show()

    if exec_loop:
        return window, app.exec()
    return window, None


if __name__ == "__main__":
    # Quick manual test runner
    win, code = start_qt_ui(exec_loop=True)
    sys.exit(code or 0)
