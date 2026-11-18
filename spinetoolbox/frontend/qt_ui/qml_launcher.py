"""Starts Spine Toolbox's main window directly in user (QML) mode, in the given project or none."""

import os
import sys
import fluentpyside
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from ...font import TOOLBOX_FONT
from ...ui_main import ToolboxUI


def _most_recent_project_dir() -> str:
    """Returns the project opened last, or an empty string if there is none or it no longer exists."""
    recents = QSettings("SpineProject", "Spine Toolbox").value("appSettings/recentProjects", defaultValue=None)
    if not recents:
        return ""
    path = str(recents).split("\n")[0].partition("<>")[2]
    return path if os.path.isdir(path) else ""


def main():
    # QApplication (not QGuiApplication) so the classic QWidget-based DB Editor can be opened in-process
    app = QApplication(sys.argv)
    app.setApplicationName("Spine Toolbox")
    TOOLBOX_FONT.get_family_from_font_database()

    # Apply FluentPySide styling before creating the window
    fluentpyside.apply()

    project_dir = sys.argv[1] if len(sys.argv) > 1 else _most_recent_project_dir()

    # the classic UI's project (self._project) is loaded lazily, only if/when the user switches to dev
    # mode (see ToolboxUI._show_dev_mode); starting directly in user mode skips that heavier machinery
    window = ToolboxUI()
    window.show()
    window.show_user_mode(project_dir)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
