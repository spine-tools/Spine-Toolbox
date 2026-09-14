import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from pathlib import Path
import fluentpyside

from .project_bridge import ProjectBridge
from ...config import PROJECT_CONFIG_DIR_NAME


def _find_project_dir(start: Path) -> Path:
    """Walks up from start looking for a .spinetoolbox project; falls back to start."""
    for candidate in (start, *start.parents):
        if (candidate / PROJECT_CONFIG_DIR_NAME).is_dir():
            return candidate
    return start


def main():
    app = QGuiApplication(sys.argv)

    # Apply FluentPySide styling before loading QML
    fluentpyside.apply()

    project_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else _find_project_dir(Path.cwd())
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