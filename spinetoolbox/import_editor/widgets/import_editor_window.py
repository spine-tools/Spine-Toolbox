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
:date:    10.6.2019
"""

import json
from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtGui import QGuiApplication, QKeySequence
from PySide2.QtWidgets import QMainWindow, QErrorMessage, QFileDialog, QDialogButtonBox, QDockWidget, QUndoStack
from ..commands import RestoreMappingsFromDict
from ...helpers import ensure_window_is_on_screen
from ...spine_io.connection_manager import ConnectionManager
from .import_editor import ImportEditor
from .import_mapping_options import ImportMappingOptions
from .import_mapping_specification import ImportMappingSpecification


class ImportEditorWindow(QMainWindow):
    """A QMainWindow to let users define Mappings for an Importer item."""

    settings_updated = Signal(dict)
    connection_failed = Signal(str)

    def __init__(self, importer, filepath, connector, connector_settings, mapping_settings, toolbox):
        """
        Args:
            importer (spinetoolbox.project_items.importer.importer.Importer): Project item that owns this preview window
            filepath (str): Importee path
            connector (SourceConnection): Asynchronous data reader
            mapping_settings (dict): Default mapping specification
            toolbox (QMainWindow): ToolboxUI class
        """
        from ..ui.import_editor_window import Ui_MainWindow  # pylint: disable=import-outside-toplevel

        super().__init__(parent=toolbox, flags=Qt.Window)
        self._importer = importer
        self._toolbox = toolbox
        self._app_settings = self._toolbox.qsettings()
        self._connection_manager = ConnectionManager(connector, connector_settings)
        self._connection_manager.source = filepath
        self._undo_stack = QUndoStack()
        self._ui_error = QErrorMessage(self)
        self._ui_error.setWindowTitle("Error")
        self._ui_error.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)
        self._insert_undo_redo_actions()
        self._mapping_specification = ImportMappingSpecification(self._ui, self._undo_stack)
        self._editor = ImportEditor(
            self._ui, self._ui_error, self._undo_stack, self._connection_manager, mapping_settings
        )
        self._ui.source_data_table.set_undo_stack(self._undo_stack, self._editor.select_table)
        self._mapping_specification.mapping_selection_changed.connect(self._editor.set_model)
        self._mapping_specification.mapping_selection_changed.connect(self._editor.set_mapping)
        self._mapping_specification.mapping_data_changed.connect(self._editor.set_mapping)
        self._mapping_options = ImportMappingOptions(self._ui, self._undo_stack)
        self._editor.source_table_selected.connect(self._mapping_specification.set_mappings_model)
        self._editor.source_table_selected.connect(self._ui.source_data_table.horizontalHeader().set_source_table)
        self._editor.source_table_selected.connect(self._ui.source_data_table.verticalHeader().set_source_table)
        self._mapping_specification.mapping_selection_changed.connect(
            self._mapping_options.set_mapping_specification_model
        )
        self._mapping_specification.about_to_undo.connect(self._editor.select_table)
        self._editor.preview_data_updated.connect(self._mapping_options.set_num_available_columns)
        self._mapping_options.about_to_undo.connect(self._mapping_specification.focus_on_changing_specification)

        self._size = None
        self.takeCentralWidget()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(f"Import Editor    -- {importer.name} --")
        self.settings_group = "mappingPreviewWindow"
        self.apply_classic_ui_style()
        self.restore_ui()
        self._button_box = QDialogButtonBox(self)
        self._button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self._ui.statusbar.addPermanentWidget(self._button_box)
        self._ui.statusbar.layout().setContentsMargins(6, 6, 6, 6)
        self._button_box.button(QDialogButtonBox.Ok).clicked.connect(self.apply_and_close)
        self._button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        self._ui.export_mappings_action.triggered.connect(self.export_mapping_to_file)
        self._ui.import_mappings_action.triggered.connect(self.import_mapping_from_file)
        self._ui.close_action.triggered.connect(self.close)
        self._connection_manager.connection_ready.connect(self.show)
        self._connection_manager.connection_failed.connect(self.connection_failed.emit)
        self._connection_manager.error.connect(self.show_error)

    def _insert_undo_redo_actions(self):
        undo_action = self._undo_stack.createUndoAction(self)
        redo_action = self._undo_stack.createRedoAction(self)
        undo_action.setShortcuts(QKeySequence.Undo)
        redo_action.setShortcuts(QKeySequence.Redo)
        actions = self._ui.edit_menu.actions()
        before = actions[0] if actions else None
        self._ui.edit_menu.insertAction(before, undo_action)
        self._ui.edit_menu.insertAction(before, redo_action)

    @Slot(str)
    def show_error(self, message):
        self._ui_error.showMessage(message)

    def restore_dock_widgets(self):
        """Docks all floating and or hidden QDockWidgets back to the window."""
        for dock in self.findChildren(QDockWidget):
            dock.setVisible(True)
            dock.setFloating(False)
            self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def begin_style_change(self):
        """Begins a style change operation."""
        self._size = self.size()
        self.restore_dock_widgets()

    def end_style_change(self):
        """Ends a style change operation."""
        qApp.processEvents()  # pylint: disable=undefined-variable
        self.resize(self._size)

    def apply_classic_ui_style(self):
        """Applies the classic UI style."""
        self.begin_style_change()
        docks = (self._ui.dockWidget_sources, self._ui.dockWidget_mappings)
        self.splitDockWidget(*docks, Qt.Horizontal)
        width = sum(d.size().width() for d in docks)
        self.resizeDocks(docks, [0.9 * width, 0.1 * width], Qt.Horizontal)
        docks = (self._ui.dockWidget_sources, self._ui.dockWidget_source_data)
        self.splitDockWidget(*docks, Qt.Vertical)
        height = sum(d.size().height() for d in docks)
        self.resizeDocks(docks, [0.1 * height, 0.9 * height], Qt.Vertical)
        self.splitDockWidget(self._ui.dockWidget_sources, self._ui.dockWidget_source_options, Qt.Horizontal)
        self.splitDockWidget(self._ui.dockWidget_mappings, self._ui.dockWidget_mapping_options, Qt.Vertical)
        self.splitDockWidget(self._ui.dockWidget_mapping_options, self._ui.dockWidget_mapping_spec, Qt.Vertical)
        docks = (self._ui.dockWidget_mapping_options, self._ui.dockWidget_mapping_spec)
        height = sum(d.size().height() for d in docks)
        self.resizeDocks(docks, [0.1 * height, 0.9 * height], Qt.Vertical)
        self.end_style_change()

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
        self._undo_stack.push(RestoreMappingsFromDict(self._editor, settings))
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
            settings = self._editor.get_settings_dict()
            json.dump(settings, file_p)
        self._ui.statusbar.showMessage(f"Mapping saved to: {filename[0]}", 10000)

    def apply_and_close(self):
        """Apply changes to mappings and close preview window."""
        settings = self._editor.get_settings_dict()
        self.settings_updated.emit(settings)
        self.close()

    def start_ui(self):
        self._connection_manager.init_connection()

    def restore_ui(self):
        """Restore UI state from previous session."""
        app_settings = self._app_settings
        app_settings.beginGroup(self.settings_group)
        window_size = app_settings.value("windowSize")
        window_pos = app_settings.value("windowPosition")
        window_state = app_settings.value("windowState")
        window_maximized = app_settings.value("windowMaximized", defaultValue='false')
        n_screens = app_settings.value("n_screens", defaultValue=1)
        app_settings.endGroup()
        original_size = self.size()
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)
        ensure_window_is_on_screen(self, original_size)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)

    def closeEvent(self, event=None):
        """Handles close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        self._editor.close_connection()
        app_settings = self._app_settings
        app_settings.beginGroup(self.settings_group)
        app_settings.setValue("windowSize", self.size())
        app_settings.setValue("windowPosition", self.pos())
        app_settings.setValue("windowState", self.saveState(version=1))
        app_settings.setValue("windowMaximized", self.windowState() == Qt.WindowMaximized)
        app_settings.setValue("n_screens", len(QGuiApplication.screens()))
        app_settings.endGroup()
        if event:
            event.accept()
