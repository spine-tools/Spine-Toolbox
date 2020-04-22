######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains ImportPreviewWindow class.

:authors: P. Savolainen (VTT), A. Soininen (VTT), P. Vennström (VTT)
:date:   10.6.2019
"""

import json
from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QGuiApplication
from PySide2.QtWidgets import QMainWindow, QDialogButtonBox, QSplitter, QFileDialog
from ..spine_io.connection_manager import ConnectionManager
from .import_preview_widget import ImportPreviewWidget


class ImportPreviewWindow(QMainWindow):
    """A QMainWindow to let users define Mappings for an Importer item.

    Args:
        importer (spinetoolbox.project_items.importer.importer.Importer): Project item that owns this preview window
        filepath (str): Importee path
        connector (SourceConnection): Asynchronous data reader
        settings (dict): Default mapping specification
        toolbox (QMainWindow): ToolboxUI class
    """

    settings_updated = Signal(dict)
    connection_failed = Signal(str)

    def __init__(self, importer, filepath, connector, settings, toolbox):
        from ..ui.import_preview_window import Ui_MainWindow

        super().__init__(parent=toolbox, flags=Qt.Window)
        self._importer = importer
        self._toolbox = toolbox
        self._qsettings = self._toolbox.qsettings()
        self._connection_manager = ConnectionManager(connector)
        self._connection_manager.source = filepath
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("Import Editor    -- {} --".format(importer.name))
        self._preview_widget = ImportPreviewWidget(self._connection_manager, parent=self)
        self._preview_widget.use_settings(settings)
        self._ui.centralwidget.layout().insertWidget(0, self._preview_widget)
        self.settings_group = "mappingPreviewWindow"
        self.restore_ui()
        self._ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.apply_and_close)
        self._ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        self._ui.actionExportMappings.triggered.connect(self.export_mapping_to_file)
        self._ui.actionImportMappings.triggered.connect(self.import_mapping_from_file)
        self._ui.actionClose.triggered.connect(self.close)
        self._connection_manager.connectionReady.connect(self.show)
        self._connection_manager.connectionFailed.connect(self.connection_failed.emit)

    def import_mapping_from_file(self):
        """Imports mapping spec from a user selected .json file to the preview window."""
        start_dir = self._toolbox.project().project_dir
        # noinspection PyCallByClass
        filename = QFileDialog.getOpenFileName(
            self, "Import mapping specification", start_dir, "Mapping options (*.json)"
        )
        if not filename[0]:
            return
        with open(filename[0]) as file_p:
            try:
                settings = json.load(file_p)
            except json.JSONDecodeError:
                self._ui.statusbar.showMessage(f"Could not open {filename[0]}", 10000)
                return
        expected_options = ("table_mappings", "table_types", "table_row_types", "table_options", "selected_tables")
        if not isinstance(settings, dict) or not any(key in expected_options for key in settings.keys()):
            self._ui.statusbar.showMessage(f"{filename[0]} does not contain mapping options", 10000)
        self._preview_widget.use_settings(settings)
        self._ui.statusbar.showMessage(f"Mapping loaded from {filename[0]}", 10000)

    def export_mapping_to_file(self):
        """Exports all mapping specs in current preview window to .json file."""
        start_dir = self._toolbox.project().project_dir
        # noinspection PyCallByClass
        filename = QFileDialog.getSaveFileName(
            self, "Export mapping spec to a file", start_dir, "Mapping options (*.json)"
        )
        if not filename[0]:
            return
        with open(filename[0], 'w') as file_p:
            settings = self._preview_widget.get_settings_dict()
            json.dump(settings, file_p)
        self._ui.statusbar.showMessage(f"Mapping saved to: {filename[0]}", 10000)

    def apply_and_close(self):
        """Apply changes to mappings and close preview window."""
        settings = self._preview_widget.get_settings_dict()
        self.settings_updated.emit(settings)
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
