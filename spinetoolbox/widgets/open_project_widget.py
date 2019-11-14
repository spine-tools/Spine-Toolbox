######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains a class for a widget that presents a 'Select Project Directory' dialog.

:author: P. Savolainen (VTT)
:date: 1.11.2019
"""

import logging
import os
from PySide2.QtWidgets import QDialog, QFileSystemModel, QAbstractItemView, QAction
from PySide2.QtCore import Qt, Slot, QDir, QStandardPaths, QTimer, QModelIndex
from PySide2.QtGui import QKeySequence
from spinetoolbox.mvcmodels.project_icon_sort_model import ProjectDirectoryIconProvider


class OpenProjectDialog(QDialog):
    """A dialog that let's user select a project to open either by choosing
    an old .proj file or by choosing a project directory."""

    def __init__(self, toolbox):
        """

        Args:
            toolbox (ToolboxUI): QMainWindow instance
        """
        from ..ui import open_project_dialog

        super().__init__(parent=toolbox, f=Qt.Dialog)  # Setting the parent inherits the stylesheet
        self._toolbox = toolbox
        # Set up the user interface from Designer file
        self.ui = open_project_dialog.Ui_Dialog()
        self.ui.setupUi(self)
        # Ensure this dialog is garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        # QActions for keyboard shortcuts
        self.go_root_action = QAction(self)
        self.go_home_action = QAction(self)
        self.go_documents_action = QAction(self)
        self.go_desktop_action = QAction(self)
        self.set_keyboard_shortcuts()
        self.selected_path = ""
        self.file_model = CustomQFileSystemModel()
        self.file_model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.file_model.setNameFilters(["*.proj"])
        self.file_model.setNameFilterDisables(False)
        self.icon_provider = ProjectDirectoryIconProvider()
        self.file_model.setIconProvider(self.icon_provider)
        self.file_model.setRootPath(QDir.rootPath())
        self.ui.treeView_file_system.setModel(self.file_model)
        # Go and select root immediately
        root_index = self.file_model.index(QDir.rootPath())
        self.ui.treeView_file_system.setCurrentIndex(root_index)
        self.ui.treeView_file_system.expand(root_index)
        self.ui.treeView_file_system.resizeColumnToContents(0)
        self.file_model.sort(0, Qt.AscendingOrder)
        self.set_selected_path(root_index)
        self.connect_signals()

    def set_keyboard_shortcuts(self):
        """Creates keyboard shortcuts for the 'Root', 'Home', etc. buttons."""
        self.go_root_action.setShortcut(QKeySequence(Qt.Key_F1))
        self.addAction(self.go_root_action)
        self.go_home_action.setShortcut(QKeySequence(Qt.Key_F2))
        self.addAction(self.go_home_action)
        self.go_documents_action.setShortcut(QKeySequence(Qt.Key_F3))
        self.addAction(self.go_documents_action)
        self.go_desktop_action.setShortcut(QKeySequence(Qt.Key_F4))
        self.addAction(self.go_desktop_action)

    def connect_signals(self):
        """Connects signals to slots."""
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.toolButton_root.clicked.connect(self.go_root)
        self.ui.toolButton_home.clicked.connect(self.go_home)
        self.ui.toolButton_documents.clicked.connect(self.go_documents)
        self.ui.toolButton_desktop.clicked.connect(self.go_desktop)
        self.ui.treeView_file_system.clicked.connect(self.set_selected_path)
        self.ui.treeView_file_system.selectionModel().currentChanged.connect(self.current_changed)
        self.go_root_action.triggered.connect(self.go_root)
        self.go_home_action.triggered.connect(self.go_home)
        self.go_documents_action.triggered.connect(self.go_documents)
        self.go_desktop_action.triggered.connect(self.go_desktop)

    @Slot("QModelIndex", "QModelIndex", name="current_changed")
    def current_changed(self, current, previous):
        """Updates selected path to line edit when scrolling items with keyboard.

        Args:
            current (QModelIndex): Currently selected index
            previous (QModelIndex): Previously selected index
        """
        self.set_selected_path(current)

    @Slot("QModelIndex", name="set_selected_path")
    def set_selected_path(self, index):
        """Sets the selected path to the line edit when the current selection in the tree view changes.

        Args:
            index (QModelIndex): The index which was mouse clicked.
        """
        if not index.isValid():
            return
        selected_path = self.file_model.filePath(index)
        self.ui.lineEdit_current_path.setText(selected_path)
        self.selected_path = selected_path

    def scroll_to_shortcut(self):
        self.ui.treeView_file_system.collapseAll()
        index = self.ui.treeView_file_system.currentIndex()
        self.ui.treeView_file_system.scrollTo(index, hint=QAbstractItemView.PositionAtTop)
        self.ui.treeView_file_system.expand(index)
        self.ui.treeView_file_system.resizeColumnToContents(0)
        self.set_selected_path(index)

    def selection(self):
        """Returns the selected path from dialog."""
        return self.selected_path

    @Slot(bool, name="go_root")
    def go_root(self, checked=False):
        """Slot for the 'Root' button. Scrolls the treeview to show and select the user's root directory."""
        root_index = self.file_model.index(QDir.rootPath())
        self.ui.treeView_file_system.setCurrentIndex(root_index)
        QTimer.singleShot(150, self.scroll_to_shortcut)

    @Slot(bool, name="go_home")
    def go_home(self, checked=False):
        """Slot for the 'Home' button. Scrolls the treeview to show and select the user's home directory."""
        home_index = self.file_model.index(QDir.homePath())
        self.ui.treeView_file_system.setCurrentIndex(home_index)
        QTimer.singleShot(150, self.scroll_to_shortcut)

    @Slot(bool, name="go_documents")
    def go_documents(self, checked=False):
        """Slot for the 'Documents' button. Scrolls the treeview to show and select the user's documents directory."""
        docs = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        if not docs:
            logging.error("No documents found on your OS")
            return
        docs_index = self.file_model.index(docs)
        self.ui.treeView_file_system.setCurrentIndex(docs_index)
        QTimer.singleShot(150, self.scroll_to_shortcut)

    @Slot(bool, name="go_desktop")
    def go_desktop(self, checked=False):
        """Slot for the 'Desktop' button. Scrolls the treeview to show and select the user's desktop directory."""
        desktop = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)  # Return a list
        if not desktop:
            logging.error("No desktop found on your OS")
            return
        desktop_index = self.file_model.index(desktop)
        self.ui.treeView_file_system.setCurrentIndex(desktop_index)
        QTimer.singleShot(150, self.scroll_to_shortcut)

    def closeEvent(self, event):
        """Handles dialog closing.

        Args:
            event (QCloseEvent): Close event
        """
        self.close()


class CustomQFileSystemModel(QFileSystemModel):
    """Custom file system model."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def columnCount(self, parent=QModelIndex()):
        """Returns one."""
        return 1
