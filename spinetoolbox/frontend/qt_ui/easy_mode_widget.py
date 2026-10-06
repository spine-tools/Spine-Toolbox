"""Embeds the easy-mode QML UI as a widget, so it can share a window with the classic Qt UI."""
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import QWidget
from .project_bridge import ProjectBridge

_QML_PATH = Path(__file__).parent / "qml" / "Main.qml"


class EasyModeWidget(QQuickWidget):
    """Hosts Main.qml and its ProjectBridge."""

    def __init__(self, project_dir: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project_bridge = ProjectBridge(project_dir, self)
        self.rootContext().setContextProperty("projectBridge", self.project_bridge)
        self.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self.setSource(QUrl.fromLocalFile(str(_QML_PATH)))
