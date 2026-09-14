"""A minimal MainWindow that mirrors the Tauri layout roughly.
This is a starting point and should be extended to hook into the shared backend.
"""
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
)
from PySide6.QtCore import Qt
from pathlib import Path


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spine Toolbox - Qt UI (prototype)")
        self.resize(1200, 800)

        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        brand = QLabel("Spine")
        brand.setObjectName("brand")
        sidebar_layout.addWidget(brand, alignment=Qt.AlignTop)
        nav = QListWidget()
        nav.addItems(["Project", "Database", "Runs", "Settings"])
        nav.setObjectName("nav-list")
        sidebar_layout.addWidget(nav)
        sidebar_layout.addStretch()

        # Workspace area
        workspace = QWidget()
        workspace.setObjectName("workspace")
        ws_layout = QVBoxLayout(workspace)
        ws_layout.setContentsMargins(24, 24, 24, 24)

        # Top bar
        topbar = QWidget()
        topbar_layout = QHBoxLayout(topbar)
        project_label = QLabel("Current Project")
        project_label.setObjectName("project-label")
        topbar_layout.addWidget(project_label)
        topbar_layout.addStretch()
        open_db_btn = QPushButton("Open Classic DB Editor")
        open_db_btn.setObjectName("classic-db-button")
        topbar_layout.addWidget(open_db_btn)
        ws_layout.addWidget(topbar)

        # Content area (left canvas + right panel)
        content = QWidget()
        content_layout = QHBoxLayout(content)
        # Canvas (graphics scene)
        from .canvas import CanvasView

        self.canvas = CanvasView()
        content_layout.addWidget(self.canvas, 3)
        # Right panel placeholder
        right_panel = QWidget()
        rp_layout = QVBoxLayout(right_panel)
        rp_label = QLabel("Inspector")
        rp_layout.addWidget(rp_label)
        rp_layout.addStretch()
        content_layout.addWidget(right_panel, 1)

        ws_layout.addWidget(content)

        root_layout.addWidget(sidebar, 0)
        root_layout.addWidget(workspace, 1)

        self.setCentralWidget(central)

        # Load style if available
        qss_path = Path(__file__).with_name("style.qss")
        if qss_path.exists():
            try:
                with qss_path.open("r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception:
                pass
        # add default nodes matching Tauri layout and auto-connect them
        self._add_default_cards()

    def _add_default_cards(self):
        # create nodes and keep references
        # linear workflow: Input -> Stack A -> Database -> Tool X -> Results
        n1 = self.canvas.add_node(40, 60, label="Input Source", kind="input")
        n2 = self.canvas.add_node(240, 60, label="Stack A", kind="stack")
        n3 = self.canvas.add_node(460, 60, label="Database 1", kind="database")
        n4 = self.canvas.add_node(680, 60, label="Tool X", kind="tool")
        n5 = self.canvas.add_node(900, 60, label="Results", kind="results")

        # auto-connect to form a ready-made linear workflow
        self.canvas.connect_nodes(n1, n2)
        self.canvas.connect_nodes(n2, n3)
        self.canvas.connect_nodes(n3, n4)
        self.canvas.connect_nodes(n4, n5)

    def _on_add_node(self):
        count = len(self.canvas.nodes)
        x = 60 + (count % 4) * 180
        y = 60 + (count // 4) * 130
        label = f"Card {count + 1}"
        self.canvas.add_node(x, y, label=label)

    def _on_connect_last_two(self):
        if len(self.canvas.nodes) >= 2:
            a = self.canvas.nodes[-2]
            b = self.canvas.nodes[-1]
            self.canvas.connect_nodes(a, b)


if __name__ == "__main__":
    # quick smoke test
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
