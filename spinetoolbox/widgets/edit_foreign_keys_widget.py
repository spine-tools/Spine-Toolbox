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
Widget shown to user when pressing Edit Foreign Keys on Data Connection item.

:author: Manuel Marin <manuelma@kth.se>
:date:   30.3.2018
"""

from copy import deepcopy
import logging
from PySide2.QtWidgets import QWidget, QStatusBar, QHeaderView, QAbstractItemView
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

    def __new__(cls, index, name):
        member = object.__new__(cls)
        member.index = index
        member.fullname = name
        return member

class EditForeignKeysWidget(QWidget):
    """A widget to allow the user to define foreign keys for a datapackage.

    Attributes:
        dc (DataConnection): Data connection object that calls this widget
    """
    def __init__(self, dc):
        """Initialize class."""
        super().__init__(f=Qt.Window)
        self.dc = dc
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
        data = self.dc.package.foreign_keys_data()
        self.original_data = deepcopy(data)
        self.fks_model.reset_model(data)
        self.fks_model.insertColumns(Header.RM.index, 1)

    def init_tableView_fks(self):
        """Initialize fhe Foreign Keys data view"""
        self.ui.tableView_fks.setItemDelegate(ComboBoxDelegate(self))
        self.ui.tableView_fks.setItemDelegateForColumn(Header.RM.index, CheckBoxDelegate(self))
        self.ui.tableView_fks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableView_fks.setModel(self.fks_model)
        self.ui.tableView_fks.setFocus()
        #self.ui.tableView_fks.setEditTriggers(QAbstractItemView.AllEditTriggers)

    def combo_items(self, index):
        """Return combobox items depending on index"""
        row = index.row()
        column = index.column()
        header = self.fks_model.headerData(column)
        if header.endswith('table'):
            items = self.dc.package.resource_names
        elif header.endswith('field'):
            header = header.replace('field', 'table')
            column = next(h.index for h in Header if h.fullname == header)
            index = self.fks_model.createIndex(row, column)
            table_name = self.fks_model.data(index)
            if table_name:
                items = self.dc.package.get_resource(table_name).schema.field_names
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
        original_table = sender.original_data
        table = sender.currentText()
        logging.debug("orig {}".format(original_table))
        logging.debug("curr {}".format(table))
        if table != original_table:
            row = sender.row
            column = sender.column
            index = self.fks_model.createIndex(row, column)
            self.fks_model.setData(index, table)
            header = self.fks_model.headerData(column)
            if header.endswith('table'):
                header = header.replace('table', 'field')
                column = next(h.index for h in Header if h.fullname == header)
                index = self.fks_model.createIndex(row, column)
                item = self.dc.package.get_resource(table).schema.field_names[0]
                self.fks_model.setData(index, item)
                self.ui.tableView_fks.update(index)

    @Slot(name='ok_clicked')
    def ok_clicked(self):
        """Udpate datapackage with Foreign Keys model."""
        new_data = deepcopy(self.fks_model.modelData())
        header = list(self.fks_model.header)
        for row in new_data:
            del row[Header.RM.index]
        del header[Header.RM.index]
        new_data = [x for x in new_data if not None in x]
        to_add = list()
        to_remove = list()
        for row in new_data:
            if row not in self.original_data:
                to_add.append(row)
        for row in self.original_data:
            if row not in new_data:
                to_remove.append(row)
        logging.debug(to_add)
        logging.debug(to_remove)
        for row in to_add:
            child_table = row[header.index(Header.CHILD_TABLE.fullname)]
            child_field = row[header.index(Header.CHILD_FIELD.fullname)]
            parent_table = row[header.index(Header.PARENT_TABLE.fullname)]
            parent_field = row[header.index(Header.PARENT_FIELD.fullname)]
            self.dc.package.add_foreign_key(child_table, child_field, parent_table, parent_field)
        for row in to_remove:
            child_table = row[header.index(Header.CHILD_TABLE.fullname)]
            child_field = row[header.index(Header.CHILD_FIELD.fullname)]
            parent_table = row[header.index(Header.PARENT_TABLE.fullname)]
            parent_field = row[header.index(Header.PARENT_FIELD.fullname)]
            self.dc.package.rm_foreign_key(child_table, child_field, parent_table, parent_field)
        if to_add or to_remove:
            self.dc.save_datapackage()
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
            index = self.fks_model.createIndex(row, Header.RM.index)
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
