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
    QTextEdit,
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
        # Canvas placeholder
        canvas = QTextEdit()
        canvas.setReadOnly(True)
        canvas.setObjectName("canvas-placeholder")
        canvas.setText("Workflow canvas placeholder\n(Implement nodes and drag/drop later)")
        content_layout.addWidget(canvas, 3)
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


if __name__ == "__main__":
    # quick smoke test
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
