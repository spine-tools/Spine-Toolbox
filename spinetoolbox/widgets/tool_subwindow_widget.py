#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
QWidget that is used to display information contained in a Tool.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   31.1.2018
"""

from PySide2.QtGui import QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Qt
from ui.subwindow_tool import Ui_Form
from config import TOOL_TREEVIEW_HEADER_SS, HEADER_POINTSIZE


class ToolSubWindowWidget(QWidget):
    """Class constructor.

    Attributes:
        item_type (str): Internal widget object type (should always be 'Tool')
    """
    def __init__(self, owner, item_type):
        """ Initialize class."""
        super().__init__()
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setObjectName(item_type)  # This is set also in setupUi(). Maybe do this only in Qt Designer.
        self._owner = owner  # Name of object that owns this object (e.g. 'Tool 1')
        self.input_file_model = QStandardItemModel()
        self.output_file_model = QStandardItemModel()
        self.ui.treeView_input_files.setModel(self.input_file_model)
        self.ui.treeView_output_files.setModel(self.output_file_model)
        self.ui.treeView_input_files.setStyleSheet(TOOL_TREEVIEW_HEADER_SS)
        self.ui.treeView_output_files.setStyleSheet(TOOL_TREEVIEW_HEADER_SS)
        self.ui.label_name.setFocus()

    def set_owner(self, owner):
        """Set owner of this SubWindowWidget.

        Args:
            owner (str): New owner
        """
        self._owner = owner

    def owner(self):
        """Return owner of this SubWindowWidget."""
        return self._owner

    def set_name_label(self, txt):
        """Set new text for the name label.

        Args:
            txt (str): Text to display in the QLabel
        """
        self.ui.label_name.setText(txt)

    def name_label(self):
        """Return name label text."""
        return self.ui.label_name.text()

    def make_header_for_input_files(self):
        """Add header to input files model."""
        h = QStandardItem("Required input files")
        # Decrease font size
        font = h.font()
        font.setPointSize(HEADER_POINTSIZE)
        h.setFont(font)
        self.input_file_model.setHorizontalHeaderItem(0, h)

    def make_header_for_output_files(self):
        """Add header to output files model."""
        h = QStandardItem("Output files")
        # Decrease font size
        font = h.font()
        font.setPointSize(HEADER_POINTSIZE)
        h.setFont(font)
        self.output_file_model.setHorizontalHeaderItem(0, h)

    def populate_input_files_list(self, items):
        """Add required Tool input files into a model.
        If items is None or an empty list, model is cleared."""
        self.input_file_model.clear()
        self.make_header_for_input_files()
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                self.input_file_model.appendRow(qitem)

    def populate_output_files_list(self, items):
        """Add Tool output files into a model.
         If items is None or an empty list, model is cleared."""
        self.output_file_model.clear()
        self.make_header_for_output_files()
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                self.output_file_model.appendRow(qitem)

    def closeEvent(self, event):
        """Hide widget and is proxy instead of closing them.

        Args:
            event (QCloseEvent): Event initiated when user clicks 'X'
        """
        event.ignore()
        self.hide()  # Hide widget and its proxy hides as well
