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
from PySide2.QtCore import Qt, Slot, Signal, QUrl
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QFileDialog
from project_item import ProjectItem
from graphics_items import DataInterfaceIcon
from helpers import create_dir


class DataInterface(ProjectItem):
    """DataInterface class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Project item name
        description (str): Project item description
        x (int): Initial icon scene X coordinate
        y (int): Initial icon scene Y coordinate
    """

    def __init__(self, toolbox, name, description, x, y):
        """Class constructor."""
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        self.item_type = "Data Interface"
        # Make directory for this item
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating directory {0} failed. Check permissions.".format(self.data_dir)
            )
        # Variables for saving selections when item is (de)activated
        self.mapping_script_path = ""
        self._graphics_item = DataInterfaceIcon(self._toolbox, x - 35, y - 35, w=70, h=70, name=self.name)
        self._sigs = self.make_signal_handler_dict()

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = dict()
        s[self._toolbox.ui.toolButton_di_open_dir.clicked] = self.open_directory
        s[self._toolbox.ui.toolButton_select_imported_file.clicked] = self.select_import_file
        s[self._toolbox.ui.pushButton_import_editor.clicked] = self.open_import_editor
        return s

    def activate(self):
        """Restores selections and connects signals."""
        self.restore_selections()
        super().connect_signals()

    def deactivate(self):
        """Saves selections and disconnects signals."""
        self.save_selections()
        if not super().disconnect_signals():
            logging.error("Item {0} deactivation failed.", self.name)
            return False
        return True

    def restore_selections(self):
        """Restores selections into shared widgets when this project item is selected."""
        self._toolbox.ui.label_di_name.setText(self.name)
        self._toolbox.ui.lineEdit_import_file_path.setText(self.mapping_script_path)

    def save_selections(self):
        """Saves selections in shared widgets for this project item into instance variables."""
        self.mapping_script_path = self._toolbox.ui.lineEdit_import_file_path.text()

    def get_icon(self):
        """Returns the graphics item representing this data interface on scene."""
        return self._graphics_item

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

    @Slot(bool, name="select_import_file")
    def select_import_file(self, checked=False):
        """Opens script path selection dialog."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(self._toolbox, "Select file to import", self.data_dir)
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        # Update UI
        self._toolbox.ui.lineEdit_import_file_path.setText(file_path)

    @Slot(bool, name="open_import_editor")
    def open_import_editor(self, checked=False):
        """Opens Import editor for the file selected into line edit."""
        importee = self._toolbox.ui.lineEdit_import_file_path.text()
        if not os.path.exists(importee):
            self._toolbox.msg_error.emit("Invalid path: {0}".format(importee))
            return
        self._toolbox.msg.emit("Opening Import editor for file: {0}".format(importee))

    def execute(self):
        """Executes this Data Interface."""
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("Executing Data Interface <b>{0}</b>".format(self.name))
        self._toolbox.msg.emit("***")
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(0)  # 0 success

    def stop_execution(self):
        """Stops executing this Data Interface."""
        self._toolbox.msg.emit("Stopping {0}".format(self.name))
