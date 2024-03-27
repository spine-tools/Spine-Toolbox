######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""A widget for inspecting project and project item versions."""
import os
import json
from PySide6.QtWidgets import QWidget, QStatusBar, QLabel
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QColor, QPainter, QBrush
from ..execution_managers import QProcessExecutionManager


LOCAL_PROJECT_REGISTRY = os.path.join("C:\\", "data", "GIT", "ProjectRegistry")
VERSION_REGISTRY_FILE = "version_registry.json"
LOCAL_PROJECT_REGISTRY_FILEPATH = os.path.join(LOCAL_PROJECT_REGISTRY, VERSION_REGISTRY_FILE)
PROJECT_REGISTRY_URL = "https://raw.githubusercontent.com/PekkaSavolainen/ProjectRegistry/main/version_registry.json"
SS = "QStatusBar:item{border: None;}"  # Removes separators between widgets in the status bar

class VersionInspectorWidget(QWidget):
    """Version Inspector widget class."""

    def __init__(self, toolbox):
        """

        Args:
            toolbox (ToolboxUI): QMainWindow instance
        """
        from ..ui import version_inspector  # pylint: disable=import-outside-toplevel

        super().__init__(parent=toolbox, f=Qt.WindowType.Window)
        self.setStyleSheet(SS)
        self._toolbox = toolbox
        self.ui = version_inspector.Ui_Form()  # Set up the user interface from Designer file.
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)  # Ensure this window gets garbage-collected when closed
        self.model = QStandardItemModel()
        self._make_statusbar()
        self.ui.tableView.setModel(self.model)
        self._git_available = self._is_git_available()
        self._reg = self._pull_version_registry()
        self._n_entries = 0
        self._rows_at_start = 0
        self._proj_dir = self._toolbox.project().project_dir
        self.setWindowTitle(f"{self.windowTitle()}" + f" - {self._proj_dir}")
        self._remote_url = self._get_remote_url()
        self.populate_model()
        self.ui.tableView.resizeColumnsToContents()
        self.connect_signals()

    def connect_signals(self):
        self.ui.pushButton_add_row.clicked.connect(self.add_row)
        self.ui.pushButton_commit.clicked.connect(self.commit)

    def populate_model(self):
        if not self._remote_url:
            self.statusbar.showMessage("Project not in Git")
            return
        items = self._toolbox.project().get_items()
        item_names = [item.name for item in items]
        item_versions = ["NA" if not item.version() else item.version() for item in items]
        self.model.setHorizontalHeaderItem(0, QStandardItem("project"))
        for j in range(len(item_names)):
            self.model.setHorizontalHeaderItem(j + 1, QStandardItem(item_names[j]))
        version_list = self._reg["projects"].get(self._remote_url)
        if not version_list:
            print("This project is not in version control")
            return
        self._n_entries = len(version_list)
        i = 0  # rows
        for entry in version_list:  # Iterate version dicts in the version list
            for k, v in entry.items():  # Iterate items in a version dict
                # print(f"k:{k} v:{v}")
                # Find column of k from header. Make a new column if not found
                unknown_entry = True
                for column_index in range(self.model.columnCount()):
                    if self.model.headerData(column_index, Qt.Orientation.Horizontal) == k:
                        self.model.setItem(i, column_index, QStandardItem(v))
                        unknown_entry = False
                if unknown_entry:
                    # Version entry k did not match any headers in the Table, make a new column
                    self.model.setHorizontalHeaderItem(self.model.columnCount(), QStandardItem(k))
                    self.model.setItem(i, self.model.columnCount()-1, QStandardItem(v))
            i+=1
        self._rows_at_start = self.model.rowCount()

    @Slot(bool)
    def add_row(self, _=False):
        if self.model.rowCount() == self._n_entries:
            self.model.setRowCount(self.model.rowCount()+1)
            return

    @Slot(bool)
    def commit(self, _=False):
        if not self._remote_url:
            return
        if self.model.rowCount() == self._rows_at_start or self._rows_at_start == 0:
            print("Make a new row first")
            return
        last_row = self.model.rowCount()-1
        new_entry = dict()
        for column in range(self.model.columnCount()):
            column_name = self.model.horizontalHeaderItem(column).data(Qt.ItemDataRole.DisplayRole)
            item = self.model.item(last_row, column)
            if not item:
                continue
            new_entry[column_name] = item.data(Qt.ItemDataRole.DisplayRole)
            print(new_entry)
        if not new_entry:
            print("Nothing to commit")
            return
        self._reg["projects"][self._remote_url].append(new_entry)
        print(f"{self._reg['projects']}")
        # Save the changes to local version_registry.json
        if not os.path.exists(LOCAL_PROJECT_REGISTRY_FILEPATH):
            print(f"{LOCAL_PROJECT_REGISTRY_FILEPATH} not found. Commit failed")
            return
        with open(LOCAL_PROJECT_REGISTRY_FILEPATH, "w") as fp:
            json.dump(self._reg, fp, indent=2)
        # Commit to Git
        if not self._stage_commit_and_push():
            print("Stage, commit or push failed")
            return
        self.statusbar.showMessage("New version committed successfully")
        self.ui.pushButton_commit.setEnabled(False)

    def _stage_commit_and_push(self):
        """Commit updated version registry file to Git."""
        manager = QProcessExecutionManager(self._toolbox, "git", args=["add", f"{VERSION_REGISTRY_FILE}"], silent=True)
        manager.start_execution(workdir=LOCAL_PROJECT_REGISTRY)
        manager.wait_for_process_finished()
        if not self._check_subprocess_finish_state(manager):
            return False
        manager = QProcessExecutionManager(self._toolbox, "git", args=["commit", "-m" "Add version"], silent=True)
        manager.start_execution(workdir=LOCAL_PROJECT_REGISTRY)
        manager.wait_for_process_finished()
        if not self._check_subprocess_finish_state(manager):
            return False
        manager = QProcessExecutionManager(self._toolbox, "git", args=["push", "origin", "main"], silent=True)
        manager.start_execution(workdir=LOCAL_PROJECT_REGISTRY)
        manager.wait_for_process_finished()
        if not self._check_subprocess_finish_state(manager):
            return False
        return True

    def _is_git_available(self):
        """Checks if git is found in user's PATH."""
        manager = QProcessExecutionManager(self._toolbox, "git", args=["--version"], silent=True)
        manager.start_execution()
        manager.wait_for_process_finished(2000)
        if not self._check_subprocess_finish_state(manager):
            self.statusbar.showMessage("Checking Git status failed")
        out = manager.process_output  # e.g. 'git version 2.31.0.windows.1'
        if not out:
            pm = self.make_circle_pixmap(QColor(Qt.GlobalColor.red))
            self.status_icon.setPixmap(pm)
            self.status_label.setText("No git found. Some features not available.")
            return False
        pm = self.make_circle_pixmap(QColor(Qt.GlobalColor.green))
        self.status_icon.setPixmap(pm)
        self.status_label.setText(out)
        return True

    def _get_remote_url(self):
        """Get project remote URL."""
        if not self._git_available:
            self.statusbar.showMessage("No Git found")
            return None
        manager = QProcessExecutionManager(self._toolbox, "git", args=["config", "--get", "remote.origin.url"], silent=True)
        manager.start_execution(workdir=self._proj_dir)
        manager.wait_for_process_finished(2000)
        if not self._check_subprocess_finish_state(manager):
            self.statusbar.showMessage("Checking project git status failed")
            return None
        out = manager.process_output  # e.g. 'https://github.com/PekkaSavolainen/VersioningProject.git'
        if not out:
            self.statusbar.showMessage("Current project not in Git")
            return None
        return out

    def _pull_version_registry(self):
        """Pulls latest changes from Project Registry repo."""
        if not self._git_available:
            return None
        manager = QProcessExecutionManager(self._toolbox, "git", args=["pull"], silent=True)
        manager.start_execution(workdir=LOCAL_PROJECT_REGISTRY)
        manager.wait_for_process_finished()
        if not self._check_subprocess_finish_state(manager):
            return None
        reg = self._load_version_registry_file()
        if reg is not None:
            self.statusbar.showMessage("Version registry loaded successfully", 5000)
        return reg

    def _check_subprocess_finish_state(self, manager):
        """Checks whether the subprocess finished successfully or not."""
        out = manager.process_output
        cmd = f"{manager.program()} {' '.join(manager.args())}"
        if manager.process_failed:  # exit_code != 0
            self.statusbar.showMessage(f"{cmd} failed. output:{out}")
            print(f"{cmd} output:{out}. error output:{manager.process_error}")
            return False
        print(f"{cmd} output: {out}")
        return True

    def _load_version_registry_file(self):
        """Opens and reads project registry file and returns it's contents."""
        try:
            with open(LOCAL_PROJECT_REGISTRY_FILEPATH, "r") as fh:
                try:
                    reg = json.load(fh)
                except json.decoder.JSONDecodeError:
                    self.statusbar.showMessage(f"Version registry file corrupted. Invalid JSON.")
                    return None
        except OSError:
            self.statusbar.showMessage(f"Version registry file missing")
            return None
        return reg

    def make_circle_pixmap(self, circle_color, r=12):
        """Draws a pixmap containing a circle filled with given color.

        Args:
            circle_color (QColor): Circle fill color
            r (int): Circle width and height
        """
        pm = QPixmap(r, r)
        pm.fill(QColor(Qt.GlobalColor.transparent))
        painter = QPainter(pm)
        painter.begin(pm)
        painter.setPen(QColor(Qt.GlobalColor.transparent))
        painter.setBrush(QBrush(circle_color))
        painter.drawEllipse(0, 0, r, r)
        painter.end()
        return pm

    def _make_statusbar(self):
        """Sets up status bar"""
        self.statusbar = QStatusBar()
        self.status_label = QLabel()
        self.status_icon = QLabel()
        self.statusbar.addPermanentWidget(self.status_icon)
        self.statusbar.addPermanentWidget(self.status_label)
        self.ui.horizontalLayout_statusbar.addWidget(self.statusbar)

    def keyPressEvent(self, e):
        """Closes widget when Escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event=None):
        """Handles close event.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()
