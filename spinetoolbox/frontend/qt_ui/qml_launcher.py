import sys

from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from pathlib import Path
import fluentpyside

from .project_bridge import ProjectBridge
from ...config import PROJECT_CONFIG_DIR_NAME


_DEFAULT_PROJECT_DIR = Path(r"C:\Users\enessi\Documents\flextool")


def _find_project_dir(start: Path) -> Path:
    """Walks up from start looking for a .spinetoolbox project; falls back to start."""
    for candidate in (start, *start.parents):
        if (candidate / PROJECT_CONFIG_DIR_NAME).is_dir():
            return candidate
    return start


def main():
    # QApplication (not QGuiApplication) so the classic QWidget-based DB Editor can be opened in-process
    app = QApplication(sys.argv)

    # Apply FluentPySide styling before loading QML
    fluentpyside.apply()

    if len(sys.argv) > 1:
        project_dir = Path(sys.argv[1])
    elif _DEFAULT_PROJECT_DIR.is_dir():
        project_dir = _DEFAULT_PROJECT_DIR
    else:
        project_dir = _find_project_dir(Path.cwd())
    project_bridge = ProjectBridge(project_dir)

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("projectBridge", project_bridge)
    qml_path = Path(__file__).parent.joinpath("qml", "Main.qml")
    engine.load(str(qml_path))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()