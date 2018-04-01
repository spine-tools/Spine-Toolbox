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
Widget shown to user when Foreign Keys are edited.

:author: Manuel Marin <manuelma@kth.se>
:date:   30.3.2018
"""

import logging
from PySide2.QtWidgets import QWidget, QStatusBar, QHeaderView
from PySide2.QtCore import Slot, Qt, QEvent
import ui.edit_foreign_keys
from config import STATUSBAR_SS
from models import MinimalTableModel
from enum import Enum
from widgets.combobox_delegate import ComboBoxDelegate
from widgets.checkbox_delegate import CheckBoxDelegate

class Header(Enum):
    """A Class for handling tableview headers"""
    RM = 0, 'Remove?'
    CHILD_TABLE = 1, 'Child table'
    CHILD_FIELD = 2, 'Child field'
    PARENT_TABLE = 3, 'Parent table'
    PARENT_FIELD = 4, 'Parent field'

    def __new__(cls, value, name):
        member = object.__new__(cls)
        member._value_ = value
        member.fullname = name
        return member

    def __int__(self):
        return self.value

class EditForeignKeysWidget(QWidget):
    """A widget to query foreign keys definiton from user.

    Attributes:
        parent (ToolboxUI): Parent widget
        project(SpineToolboxProject): Project where to add the new Tool
    """
    def __init__(self, parent, project):
        """Initialize class."""
        super().__init__(f=Qt.Window)
        self._parent = parent
        self._project = project
        #  Set up the user interface from Designer.
        self.ui = ui.edit_foreign_keys.Ui_Form()
        self.ui.setupUi(self)
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # Init
        self.init_fks_model()
        self.init_tableView_fks()
        self.connect_signals()
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def init_fks_model(self):
        """Initialize the Foreign Keys data model"""
        self.fks_model = MinimalTableModel()
        for header in Header:
            self.fks_model.header.append(header.fullname)
        new_data = self._parent.foreign_keys_data()
        self.fks_model.reset_model(new_data)
        self.fks_model.insertColumns(int(Header.RM), 1)

    def init_tableView_fks(self):
        """Initialize fhe Foreign Keys data view"""
        self.ui.tableView_fks.setItemDelegate(ComboBoxDelegate(self))
        self.ui.tableView_fks.setItemDelegateForColumn(int(Header.RM), CheckBoxDelegate(self))
        self.ui.tableView_fks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableView_fks.setModel(self.fks_model)
        self.ui.tableView_fks.setFocus()

    def combo_items(self, index):
        """Return combobox items depending on index"""
        row = index.row()
        column = index.column()
        header = self.fks_model.headerData(column)
        if header.endswith('table'):
            items = self._parent.package.resource_names
        elif header.endswith('field'):
            index = self.fks_model.createIndex(row, column-1)
            table_name = self.fks_model.data(index)
            if table_name:
                items = self._parent.package.get_resource(table_name).schema.field_names
            else:
                header = header.replace('field', 'table')
                msg = "{} not selected. Select one first.".format(header)
                self.statusbar.showMessage(msg, 3000)
                items = None
        return items

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.tableView_fks.itemDelegate().commitData.connect(self.data_commited)
        self.ui.toolButton_add_fk.clicked.connect(self.add_fk_clicked)
        self.ui.toolButton_rm_fks.clicked.connect(self.rm_fks_clicked)
        self.ui.pushButton_ok.clicked.connect(self.ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)

    @Slot(int, name='data_commited')
    def data_commited(self, sender):
        """Whenever the table combobox changes, update the field combobox view"""
        row = sender.row
        column = sender.column
        header = self.fks_model.headerData(column)
        if header.endswith('table'):
            table = sender.currentText()
            item = self._parent.package.get_resource(table).schema.field_names[0]
            index = self.fks_model.createIndex(row, column+1)
            self.fks_model.setData(index, item)
            self.ui.tableView_fks.update(index)

    @Slot(name='ok_clicked')
    def ok_clicked(self):
        """Udpate datapackage with Foreign Keys model."""
        self._parent.clear_foreign_keys()
        for row in range(self.fks_model.rowCount()):
            index = self.fks_model.createIndex(row, 0)
            row_data = self.fks_model.rowData(index)
            if None in [x for i,x in enumerate(row_data) if i != int(Header.RM)]:
                continue
            child_table = row_data[int(Header.CHILD_TABLE)]
            child_field = row_data[int(Header.CHILD_FIELD)]
            parent_table = row_data[int(Header.PARENT_TABLE)]
            parent_field = row_data[int(Header.PARENT_FIELD)]
            self._parent.add_foreign_key(child_table, child_field, parent_table, parent_field)
        self._parent.save_datapackage()
        self.close()

    @Slot(name='add_fk_clicked')
    def add_fk_clicked(self):
        """Creates new empty row in the Foreign Keys model."""
        self.fks_model.insertRows(self.fks_model.rowCount(), 1)

    @Slot(name='rm_fks_clicked')
    def rm_fks_clicked(self):
        """Removes selected rows from Foreign Keys model."""
        new_data = []
        for row in range(self.fks_model.rowCount()):
            index = self.fks_model.createIndex(row, int(Header.RM))
            if not self.fks_model.data(index):
                new_data.append(self.fks_model.rowData(index))
        self.fks_model.reset_model(new_data)

    def keyPressEvent(self, e):
        """Close Setup form when escape key is pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()
