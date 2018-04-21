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
QWidget that is used as an internal widget for a Data Store QGraphicsProxyWidget.

:author: Manuel Marin <manuelma@kth.se>
:date:   19.4.2018
"""

from PySide2.QtGui import QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Qt
from ui.subwindow_data_store import Ui_Form
from config import DS_TREEVIEW_HEADER_SS, HEADER_POINTSIZE
import logging


class DataStoreWidget(QWidget):
    """Class constructor.

    Attributes:
        item_type (str): Internal widget object type (should always be 'Data Store')
    """

    def __init__(self, owner, item_type):
        """ Initialize class."""
        super().__init__()
        # Setup UI from Qt Designer file
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setObjectName(item_type)  # This is set also in setupUi(). Maybe do this only in Qt Designer.
        self._owner = owner  # Name of object that owns this object (e.g. 'DC 1')
        self.reference_model = QStandardItemModel()  # References to databases
        self.data_model = QStandardItemModel()  # Paths of project internal Spine objects. These are found in DS data directory.
        self.ui.treeView_references.setModel(self.reference_model)
        self.ui.treeView_data.setModel(self.data_model)
        self.ui.treeView_references.setStyleSheet(DS_TREEVIEW_HEADER_SS)
        self.ui.treeView_data.setStyleSheet(DS_TREEVIEW_HEADER_SS)
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

    def make_header_for_references(self):
        """Add header to files model. I.e. External Data Connection files."""
        h = QStandardItem("References")
        # Decrease font size
        font = h.font()
        font.setPointSize(HEADER_POINTSIZE)
        h.setFont(font)
        self.reference_model.setHorizontalHeaderItem(0, h)

    def make_header_for_data(self):
        """Add header to data model. I.e. Internal Data Connection files."""
        h = QStandardItem("Data")
        # Decrease font size
        font = h.font()
        font.setPointSize(HEADER_POINTSIZE)
        h.setFont(font)
        self.data_model.setHorizontalHeaderItem(0, h)

    def populate_reference_list(self, items):
        """List file references in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.reference_model.clear()
        self.make_header_for_references()
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                self.reference_model.appendRow(qitem)

    def populate_data_list(self, items):
        """List project internal data (files) in QTreeView.
        If items is None or empty list, model is cleared.
        """
        self.data_model.clear()
        self.make_header_for_data()
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setFlags(~Qt.ItemIsEditable)
                self.data_model.appendRow(qitem)

    def closeEvent(self, event):
        """Hide widget and is proxy instead of closing them.

        Args:
            event (QCloseEvent): Event initiated when user clicks 'X'
        """
        event.ignore()
        self.hide()  # Hide widget and its proxy hides as well

    def parent(self):
        """Return embedding QGraphicsProxyWindow"""
        return self.graphicsProxyWidget()
