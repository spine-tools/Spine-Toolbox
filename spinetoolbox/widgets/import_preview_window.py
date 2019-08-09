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
Contains DataInterface class.

:authors: P. Savolainen (VTT)
:date:   10.6.2019
"""

from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QGuiApplication
from PySide2.QtWidgets import QMainWindow, QDialogButtonBox, QWidget, QVBoxLayout, QSplitter
from spine_io.connection_manager import ConnectionManager
from spine_io.widgets.import_preview_widget import ImportPreviewWidget


class ImportPreviewWindow(QMainWindow):
    """
    A QMainWindow to let users define Mappings for a Data Interface item.
    """

    settings_updated = Signal(dict)
    connection_failed = Signal(str)

    def __init__(self, data_interface, filepath, connector, settings):
        super().__init__(flags=Qt.Window)
        self._data_interface = data_interface
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("Data interface import preview    -- {} --".format(data_interface.name))
        self._qsettings = data_interface._toolbox._qsettings

        self._connection_manager = ConnectionManager(connector)
        self._connection_manager._source = filepath
        self._preview_widget = ImportPreviewWidget(self._connection_manager, parent=self)
        self._preview_widget.use_settings(settings)
        self._dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Apply | QDialogButtonBox.Cancel)
        self._dialog_buttons.button(QDialogButtonBox.Ok).setText("Save and close")
        self._dialog_buttons.button(QDialogButtonBox.Apply).setText("Save")
        self._qw = QWidget()
        self._qw.setLayout(QVBoxLayout())
        self._qw.layout().addWidget(self._preview_widget)
        self._qw.layout().addWidget(self._dialog_buttons)
        self.setCentralWidget(self._qw)

        self.settings_group = "mappingPreviewWindow"
        self.restore_ui()

        self._dialog_buttons.button(QDialogButtonBox.Ok).clicked.connect(self.save_and_close)
        self._dialog_buttons.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        self._dialog_buttons.button(QDialogButtonBox.Apply).clicked.connect(self.save)

        self._connection_manager.connectionReady.connect(self.show)
        self._connection_manager.connectionFailed.connect(self.connection_failed.emit)

    def save(self):
        settings = self._preview_widget.get_settings_dict()
        self.settings_updated.emit(settings)

    def save_and_close(self):
        self.save()
        self.close()

    def start_ui(self):
        self._connection_manager.init_connection()

    def restore_ui(self):
        """Restore UI state from previous session."""
        qsettings = self._qsettings
        qsettings.beginGroup(self.settings_group)
        window_size = qsettings.value("windowSize")
        window_pos = qsettings.value("windowPosition")
        window_state = qsettings.value("windowState")
        window_maximized = qsettings.value("windowMaximized", defaultValue='false')
        n_screens = qsettings.value("n_screens", defaultValue=1)
        splitter_state = {}
        for splitter in self.findChildren(QSplitter):
            splitter_state[splitter] = qsettings.value(splitter.objectName() + "_splitterState")
        qsettings.endGroup()
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        for splitter, state in splitter_state.items():
            if state:
                splitter.restoreState(state)
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """

        # save qsettings
        qsettings = self._qsettings
        qsettings.beginGroup(self.settings_group)
        for splitter in self.findChildren(QSplitter):
            qsettings.setValue(splitter.objectName() + "_splitterState", splitter.saveState())
        qsettings.setValue("windowSize", self.size())
        qsettings.setValue("windowPosition", self.pos())
        qsettings.setValue("windowState", self.saveState(version=1))
        if self.windowState() == Qt.WindowMaximized:
            qsettings.setValue("windowMaximized", True)
        else:
            qsettings.setValue("windowMaximized", False)
        qsettings.endGroup()
        if event:
            event.accept()
