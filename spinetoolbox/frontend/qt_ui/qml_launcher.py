import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from pathlib import Path
import fluentpyside


def main():
    app = QGuiApplication(sys.argv)

    # Apply FluentPySide styling before loading QML
    fluentpyside.apply()

    engine = QQmlApplicationEngine()
    qml_path = Path(__file__).parent.joinpath("qml", "Main.qml")
    engine.load(str(qml_path))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()