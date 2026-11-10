"""Starts Spine Toolbox's main window directly in user (QML) mode, in the given project or none."""

import sys
import fluentpyside
from PySide6.QtWidgets import QApplication
from ...font import TOOLBOX_FONT
from ...ui_main import ToolboxUI


def main():
    # QApplication (not QGuiApplication) so the classic QWidget-based DB Editor can be opened in-process
    app = QApplication(sys.argv)
    app.setApplicationName("Spine Toolbox")
    TOOLBOX_FONT.get_family_from_font_database()

    # Apply FluentPySide styling before creating the window
    fluentpyside.apply()

    project_dir = sys.argv[1] if len(sys.argv) > 1 else ""

    # the classic UI's project (self._project) is loaded lazily, only if/when the user switches to dev
    # mode (see ToolboxUI._show_dev_mode); starting directly in user mode skips that heavier machinery
    window = ToolboxUI()
    window.show()
    window.show_user_mode(project_dir)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
