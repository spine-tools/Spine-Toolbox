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

import logging
import os
from PySide2.QtCore import Qt, Slot, QUrl, QFileInfo
from PySide2.QtGui import QDesktopServices, QStandardItem, QStandardItemModel
from PySide2.QtWidgets import QFileIconProvider, QMainWindow, QListWidget, QDialog, QVBoxLayout, QDialogButtonBox
from project_item import ProjectItem
from graphics_items import DataInterfaceIcon
from helpers import create_dir, create_log_file_timestamp
from spine_io.importers.csv_reader import CSVConnector
from spine_io.importers.excel_reader import ExcelConnector
from widgets.import_preview_window import ImportPreviewWindow


class DataInterface(ProjectItem):
    """DataInterface class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Project item name
        description (str): Project item description
        mappings (dict): dict with mapping settings
        x (int): Initial icon scene X coordinate
        y (int): Initial icon scene Y coordinate
    """

    def __init__(self, toolbox, name, description, mappings, x, y):
        """Class constructor."""
        super().__init__(toolbox, name, description)
        self._project = self._toolbox.project()
        self.item_type = "Data Interface"
        # Make data directory and logs subdirectory for this item
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        self.logs_dir = os.path.join(self.data_dir, "logs")
        try:
            create_dir(self.data_dir)
            create_dir(self.logs_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating directory {0} failed. Check permissions.".format(self.data_dir)
            )
        # Variables for saving selections when item is (de)activated
        self.settings = mappings
        self.file_model = QStandardItemModel()
        self.all_files = []  # All source files
        self.unchecked_files = []  # Unchecked source files
        self._graphics_item = DataInterfaceIcon(self._toolbox, x - 35, y - 35, w=70, h=70, name=self.name)
        self._sigs = self.make_signal_handler_dict()
        # connector class
        self._preview_widget = {}  # Key is the filepath, value is the ImportPreviewWindow instance

    @Slot(QStandardItem, name="_handle_file_model_item_changed")
    def _handle_file_model_item_changed(self, item):
        if item.checkState() == Qt.Checked:
            self.unchecked_files.remove(item.text())
            self._toolbox.msg.emit(
                "<b>{0}:</b> Source file '{1}' will be processed at execution.".format(self.name, item.text())
            )
        elif item.checkState() != Qt.Checked:
            self.unchecked_files.append(item.text())
            self._toolbox.msg.emit(
                "<b>{0}:</b> Source file '{1}' will *NOT* be processed at execution.".format(self.name, item.text())
            )

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = dict()
        s[self._toolbox.ui.toolButton_di_open_dir.clicked] = self.open_directory
        s[self._toolbox.ui.pushButton_import_editor.clicked] = self._handle_import_editor_clicked
        s[self._toolbox.ui.treeView_data_interface_files.doubleClicked] = self._handle_files_double_clicked
        return s

    def activate(self):
        """Restores selections and connects signals."""
        self.restore_selections()
        super().connect_signals()

    def deactivate(self):
        """Saves selections and disconnects signals."""
        self.save_selections()
        if not super().disconnect_signals():
            logging.error("Item %s deactivation failed.", self.name)
            return False
        return True

    def restore_selections(self):
        """Restores selections into shared widgets when this project item is selected."""
        self._toolbox.ui.label_di_name.setText(self.name)
        self._toolbox.ui.treeView_data_interface_files.setModel(self.file_model)
        self.file_model.itemChanged.connect(self._handle_file_model_item_changed)

    def save_selections(self):
        """Saves selections in shared widgets for this project item into instance variables."""
        self._toolbox.ui.treeView_data_interface_files.setModel(None)
        self.file_model.itemChanged.disconnect(self._handle_file_model_item_changed)

    def update_name_label(self):
        """Update Data Interface tab name label. Used only when renaming project items."""
        self._toolbox.ui.label_di_name.setText(self.name)

    @Slot(bool, name="open_directory")
    def open_directory(self, checked=False):
        """Opens file explorer in Data Interface directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    @Slot(bool, name="_handle_import_editor_clicked")
    def _handle_import_editor_clicked(self, checked=False):
        """Opens Import editor for the file selected in list view."""
        index = self._toolbox.ui.treeView_data_interface_files.currentIndex()
        self.open_import_editor(index)

    @Slot("QModelIndex", name="_handle_files_double_clicked")
    def _handle_files_double_clicked(self, index):
        """Opens Import editor for the double clicked index."""
        self.open_import_editor(index)

    def open_import_editor(self, index):
        """Opens Import editor for the given index."""
        importee = index.data()
        if importee is None:
            self._toolbox.msg_error.emit("Please select a source file from the list first.")
            return
        if not os.path.exists(importee):
            self._toolbox.msg_error.emit("Invalid path: {0}".format(importee))
            return
        # Raise current form for the selected file if any
        preview_widget = self._preview_widget.get(importee, None)
        if preview_widget:
            if preview_widget.windowState() & Qt.WindowMinimized:
                # Remove minimized status and restore window with the previous state (maximized/normal state)
                preview_widget.setWindowState(preview_widget.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
                preview_widget.activateWindow()
            else:
                preview_widget.raise_()
            return
        # Create a new form for the selected file
        settings = self.settings.setdefault(importee, {})
        # Try and get connector from settings
        source_type = settings.get("source_type", None)
        if source_type is not None:
            connector = eval(source_type)
        else:
            # Ask user
            connector = self.get_connector(importee)
            if not connector:
                # Aborted by the user
                return
        self._toolbox.msg.emit("Opening Import editor for file: {0}".format(importee))
        preview_widget = self._preview_widget[importee] = ImportPreviewWindow(self, importee, connector, settings)
        preview_widget.settings_updated.connect(lambda s, importee=importee: self.save_settings(s, importee))
        preview_widget.connection_failed.connect(lambda m, importee=importee: self._connection_failed(m, importee))
        preview_widget.destroyed.connect(lambda o=None, importee=importee: self._preview_destroyed(importee))
        preview_widget.start_ui()

    def get_connector(self, importee):
        """Shows a QDialog to select a connector for the given source file.
        Mimics similar routine in `spine_io.widgets.import_widget.ImportDialog`
        """
        connector_list = [CSVConnector, ExcelConnector]  # TODO: add others as needed
        connector_names = [c.DISPLAY_NAME for c in connector_list]
        dialog = QDialog(self._toolbox)
        dialog.setLayout(QVBoxLayout())
        connector_list_wg = QListWidget()
        connector_list_wg.addItems(connector_names)
        # Set current item in `connector_list_wg` based on file extension
        _filename, file_extension = os.path.splitext(importee)
        if file_extension.lower().startswith(".xls"):
            row = connector_list.index(ExcelConnector)
        elif file_extension.lower() == ".csv":
            row = connector_list.index(CSVConnector)
        else:
            row = None
        if row:
            connector_list_wg.setCurrentRow(row)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).clicked.connect(dialog.accept)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(dialog.reject)
        connector_list_wg.doubleClicked.connect(dialog.accept)
        dialog.layout().addWidget(connector_list_wg)
        dialog.layout().addWidget(button_box)
        _dirname, filename = os.path.split(importee)
        dialog.setWindowTitle("Select connector for '{}'".format(filename))
        answer = dialog.exec_()
        if answer:
            row = connector_list_wg.currentIndex().row()
            return connector_list[row]

    def select_connector_type(self, index):
        """Opens dialog to select connector type for the given index."""
        importee = index.data()
        connector = self.get_connector(importee)
        if not connector:
            # Aborted by the user
            return
        settings = self.settings.setdefault(importee, {})
        settings["source_type"] = connector.__name__

    def _connection_failed(self, msg, importee):
        self._toolbox.msg.emit(msg)
        preview_widget = self._preview_widget.pop(importee, None)
        if preview_widget:
            preview_widget.close()

    def save_settings(self, settings, importee):
        self.settings[importee].update(settings)

    def _preview_destroyed(self, importee):
        preview_widget = self._preview_widget.pop(importee, None)

    def update_file_model(self, items):
        """Add given list of items to the file model. If None or
        an empty list given, the model is cleared."""
        self.all_files = items
        self.file_model.clear()
        self.file_model.setHorizontalHeaderItem(0, QStandardItem("Source files"))  # Add header
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setEditable(False)
                qitem.setCheckable(True)
                if item in self.unchecked_files:
                    qitem.setCheckState(Qt.Unchecked)
                else:
                    qitem.setCheckState(Qt.Checked)
                qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                self.file_model.appendRow(qitem)

    def execute(self):
        """Executes this Data Interface."""
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("Executing Data Interface <b>{0}</b>".format(self.name))
        self._toolbox.msg.emit("***")

        inst = self._toolbox.project().execution_instance
        all_data = []
        all_errors = []

        checked_files = [f for f in self.all_files if f not in self.unchecked_files]
        for source in checked_files:
            settings = self.settings.get(source, None)
            if settings is None:
                self._toolbox.msg_warning.emit(
                    "<b>{0}:</b> There are no mappings defined for {1}, moving on...".format(self.name, source)
                )
                continue
            source_type = settings["source_type"]
            connector = eval(source_type)()
            connector.connect_to_source(source)
            data, errors = connector.get_mapped_data(settings["table_mappings"], settings["table_options"], max_rows=-1)
            self._toolbox.msg.emit(
                "<b>{0}:</b> Read {1} data from {2} with {3} errors".format(
                    self.name, sum(len(d) for d in data.values()), source, len(errors)
                )
            )
            all_data.append(data)
            all_errors.extend(errors)
        if all_errors:
            # Log errors in a time stamped file into the logs directory
            timestamp = create_log_file_timestamp()
            logfilepath = os.path.abspath(os.path.join(self.logs_dir, timestamp + "_error.log"))
            with open(logfilepath, 'w') as f:
                for err in all_errors:
                    f.write("{}\n".format(err))
            # Make error log file anchor with path as tooltip
            logfile_anchor = (
                "<a style='color:#BB99FF;' title='" + logfilepath + "' href='file:///" + logfilepath + "'>error log</a>"
            )
            self._toolbox.msg_error.emit(
                "There where errors while executing <b>{0}</b>. {1}".format(self.name, logfile_anchor)
            )
            self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(-1)
        if all_data:
            # Add mapped data to a dict in the execution instance.
            # If execution reaches a Data Store, the mapped data will be imported into the corresponding url
            inst.add_di_data(self.name, all_data)
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(0)  # 0 success

    def stop_execution(self):
        """Stops executing this Data Interface."""
        self._toolbox.msg.emit("Stopping {0}".format(self.name))

    def simulate_execution(self, inst):
        """Simulates executing this Item."""
        super().simulate_execution(inst)
        file_list = inst.dc_refs_at_sight(self.name).union(inst.dc_files_at_sight(self.name))
        self.update_file_model(file_list)
        if not file_list:
            self.add_notification(
                "This Data Interface does not have any input data. "
                "Connect Data Connections to this Data Interface to use their data as input."
            )

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        d = super().item_dict()
        d["mappings"] = self.settings
        return d
