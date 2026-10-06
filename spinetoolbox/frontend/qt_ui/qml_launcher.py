"""Starts Spine Toolbox's main window directly in easy (QML) mode, in the given or default project."""
import sys

from PySide6.QtWidgets import QApplication

from pathlib import Path
import fluentpyside

from ...config import PROJECT_CONFIG_DIR_NAME
from ...font import TOOLBOX_FONT
from ...ui_main import ToolboxUI


_DEFAULT_PROJECT_DIR = Path(r"C:\Users\enessi\flextool")


def _find_project_dir(start: Path) -> Path:
    """Walks up from start looking for a .spinetoolbox project; falls back to start."""
    for candidate in (start, *start.parents):
        if (candidate / PROJECT_CONFIG_DIR_NAME).is_dir():
            return candidate
    return start


def main():
    # QApplication (not QGuiApplication) so the classic QWidget-based DB Editor can be opened in-process
    app = QApplication(sys.argv)
    app.setApplicationName("Spine Toolbox")
    TOOLBOX_FONT.get_family_from_font_database()

    # Apply FluentPySide styling before creating the window
    fluentpyside.apply()

    if len(sys.argv) > 1:
        project_dir = Path(sys.argv[1])
    elif _DEFAULT_PROJECT_DIR.is_dir():
        project_dir = _DEFAULT_PROJECT_DIR
    else:
        project_dir = _find_project_dir(Path.cwd())

    # the classic UI's project (self._project) is loaded lazily, only if/when the user switches to dev
    # mode (see ToolboxUI._show_dev_mode); starting directly in easy mode skips that heavier machinery
    window = ToolboxUI()
    window.show()
    window._show_easy_mode(str(project_dir))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
