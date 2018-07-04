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
Widget shown to user when pressing Edit Keys on Data Connection item.

:author: Manuel Marin <manuelma@kth.se>
:date:   30.3.2018
"""

import logging
from copy import deepcopy
from PySide2.QtWidgets import QWidget, QStatusBar, QHeaderView
from PySide2.QtCore import Slot, Qt, QEvent
import ui.edit_datapackage_keys
from config import STATUSBAR_SS
from models import MinimalTableModel
from enum import Enum
from widgets.combobox_delegate import ComboBoxDelegate
from widgets.checkbox_delegate import CheckBoxDelegate


class PrimaryKeysHeader(Enum):
    """A Class for handling primary key tableview headers."""
    RM = 0, 'Select'
    TABLE = 1, 'Table'
    FIELD = 2, 'Field'

    def __init__(self, index, fullname):
        self.index = index
        self.fullname = fullname

class ForeignKeysHeader(Enum):
    """A Class for handling foreign key tableview headers."""
    RM = 0, 'Select'
    CHILD_TABLE = 1, 'Child table'
    CHILD_FIELD = 2, 'Child field'
    PARENT_TABLE = 3, 'Parent table'
    PARENT_FIELD = 4, 'Parent field'

    def __init__(self, index, fullname):
        self.index = index
        self.fullname = fullname

class EditDatapackageKeysWidget(QWidget):
    """A widget to request the user to define keys for a datapackage.

    Attributes:
        dc (DataConnection): Data connection object that calls this widget
    """
    def __init__(self, dc):
        """Initialize class."""
        super().__init__()
        self.dc = dc
        #  Set up the user interface from Designer.
        self.ui = ui.edit_datapackage_keys.Ui_Form()
        self.ui.setupUi(self)
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # Instance variables
        self.pks_model = None
        self.fks_model = None
        self.original_pk_data = None
        self.original_fk_data = None
        # Init
        self.init_models()
        self.init_tableviews()
        self.connect_signals()
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def init_models(self):
        """Initialize Keys data model."""
        # primary keys
        self.pks_model = MinimalTableModel()
        for header in PrimaryKeysHeader:
            self.pks_model.header.append(header.fullname)
        data = self.dc.package.primary_keys_data()
        self.original_pk_data = deepcopy(data)
        self.pks_model.reset_model(data)
        self.pks_model.set_tool_tip("<p>Double click to start editing.")
        self.pks_model.insertColumns(PrimaryKeysHeader.RM.index, 1)
        # foreign keys
        self.fks_model = MinimalTableModel()
        for header in ForeignKeysHeader:
            self.fks_model.header.append(header.fullname)
        data = self.dc.package.foreign_keys_data()
        self.original_fk_data = deepcopy(data)
        self.fks_model.reset_model(data)
        self.fks_model.set_tool_tip("<p>Double click to start editing.")
        self.fks_model.insertColumns(ForeignKeysHeader.RM.index, 1)

    def init_tableviews(self):
        """Initialize Keys data view."""
        # primary keys
        self.ui.tableView_pks.setItemDelegate(ComboBoxDelegate(self))
        self.ui.tableView_pks.setItemDelegateForColumn(PrimaryKeysHeader.RM.index, CheckBoxDelegate(self))
        self.ui.tableView_pks.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableView_pks.setModel(self.pks_model)
        self.ui.tableView_pks.setup_combo_items = self.pk_setup_combo_items
        self.resize_tableview_pks()
        # foreign keys
        self.ui.tableView_fks.setItemDelegate(ComboBoxDelegate(self))
        self.ui.tableView_fks.setItemDelegateForColumn(ForeignKeysHeader.RM.index, CheckBoxDelegate(self))
        self.ui.tableView_fks.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tableView_fks.setModel(self.fks_model)
        self.ui.tableView_fks.setup_combo_items = self.fk_setup_combo_items
        self.resize_tableview_fks()

    def resize_tableview_pks(self):
        self.ui.tableView_pks.resizeColumnsToContents()
        new_width = 2
        for h in PrimaryKeysHeader:
            new_width += self.ui.tableView_pks.columnWidth(h.index)
        self.ui.tableView_pks.setMinimumWidth(new_width)

    def resize_tableview_fks(self):
        self.ui.tableView_fks.resizeColumnsToContents()
        new_width = 2
        for h in ForeignKeysHeader:
            new_width += self.ui.tableView_fks.columnWidth(h.index)
        self.ui.tableView_fks.setMinimumWidth(new_width)

    def connect_signals(self):
        """Connect signals to slots."""
        # primary keys
        self.ui.tableView_pks.itemDelegate().closeEditor.connect(self.pk_data_committed)
        column = PrimaryKeysHeader.RM.index
        self.ui.tableView_pks.itemDelegateForColumn(column).commit_data.connect(self.pk_checkbox_toggled)
        self.ui.toolButton_add_pk.clicked.connect(self.add_pk_clicked)
        self.ui.toolButton_rm_pks.clicked.connect(self.rm_pks_clicked)
        # foreign keys
        self.ui.tableView_fks.itemDelegate().closeEditor.connect(self.fk_data_committed)
        column = ForeignKeysHeader.RM.index
        self.ui.tableView_fks.itemDelegateForColumn(column).commit_data.connect(self.fk_checkbox_toggled)
        self.ui.toolButton_add_fk.clicked.connect(self.add_fk_clicked)
        self.ui.toolButton_rm_fks.clicked.connect(self.rm_fks_clicked)
        # common
        self.ui.pushButton_ok.clicked.connect(self.ok_clicked)
        self.ui.pushButton_cancel.clicked.connect(self.close)

    def pk_setup_combo_items(self, index):
        """Determine combobox items depending on index and store them in Qt.UserRole"""
        row = index.row()
        column = index.column()
        header = self.pks_model.headerData(column)
        if header == 'Table':
            items = self.dc.package.resource_names
            # filter out items already in the model
            column_data = self.pks_model.columnData(column)
            items = [i for i in items if i not in column_data]
        elif header == 'Field':
            header = 'Table'
            next_column = next(h.index for h in PrimaryKeysHeader if h.fullname == header)
            next_index = self.pks_model.index(row, next_column)
            table_name = self.pks_model.data(next_index)
            if table_name:
                items = self.dc.package.get_resource(table_name).schema.field_names
            else:
                msg = "{} not selected. Select one first.".format(header)
                self.statusbar.showMessage(msg, 3000)
                items = None
        self.pks_model.setData(index, items, Qt.UserRole)

    def fk_setup_combo_items(self, index):
        """Determine combobox items depending on index and store them in Qt.UserRole"""
        row = index.row()
        column = index.column()
        header = self.fks_model.headerData(column)
        if header.endswith('table'):
            items = self.dc.package.resource_names
        elif header.endswith('field'):
            header = header.replace('field', 'table')
            next_column = next(h.index for h in ForeignKeysHeader if h.fullname == header)
            next_index = self.fks_model.index(row, next_column)
            table_name = self.fks_model.data(next_index)
            if table_name:
                items = self.dc.package.get_resource(table_name).schema.field_names
            else:
                msg = "{} not selected. Select one first.".format(header)
                self.statusbar.showMessage(msg, 3000)
                items = None
        self.fks_model.setData(index, items, Qt.UserRole)

    @Slot("QModelIndex", name='pk_checkbox_toggled')
    def pk_checkbox_toggled(self, index):
        """Whenever the checkbox is toggled, also toggle the value in the model."""
        d = self.pks_model.data(index)
        self.pks_model.setData(index, not d)


    @Slot("QModelIndex", name='fk_checkbox_toggled')
    def fk_checkbox_toggled(self, index):
        """Whenever the checkbox is toggled, also toggle the value in the model."""
        d = self.fks_model.data(index)
        self.fks_model.setData(index, not d)


    @Slot("QWidget", name='pk_data_committed')
    def pk_data_committed(self, editor):
        """Whenever the table combobox changes, update the field combobox view"""
        previous_table = editor.previous_data
        current_table = editor.currentText()
        # logging.debug("prev {}".format(previous_table))
        # logging.debug("curr {}".format(current_table))
        if current_table != previous_table:
            editor.previous_data = current_table
            row = editor.row
            column = editor.column
            index = self.pks_model.index(row, column)
            self.pks_model.setData(index, current_table)
            header = self.pks_model.headerData(column)
            if header == 'Table':
                header = 'Field'
                column = next(h.index for h in PrimaryKeysHeader if h.fullname == header)
                index = self.pks_model.index(row, column)
                item = self.dc.package.get_resource(current_table).schema.field_names[0]
                self.pks_model.setData(index, item)
                self.ui.tableView_pks.update(index)
        self.resize_tableview_pks()

    @Slot("QWidget", name='fk_data_committed')
    def fk_data_committed(self, editor):
        """Whenever table combobox changes, update field combobox view."""
        previous_table = editor.previous_data
        current_table = editor.currentText()
        # logging.debug("prev {}".format(previous_table))
        # logging.debug("curr {}".format(current_table))
        if current_table != previous_table:
            editor.previous_data = current_table
            row = editor.row
            column = editor.column
            index = self.fks_model.index(row, column)
            self.fks_model.setData(index, current_table)
            header = self.fks_model.headerData(column)
            if header.endswith('table'):
                header = header.replace('table', 'field')
                column = next(h.index for h in ForeignKeysHeader if h.fullname == header)
                index = self.fks_model.index(row, column)
                item = self.dc.package.get_resource(current_table).schema.field_names[0]
                self.fks_model.setData(index, item)
                self.ui.tableView_fks.update(index)
        self.resize_tableview_fks()

    @Slot(name='ok_clicked')
    def ok_clicked(self):
        """Update datapackage with Keys model."""
        # primary keys
        new_data = deepcopy(self.pks_model.modelData())
        header = list(self.pks_model.header)
        for row in new_data:
            del row[PrimaryKeysHeader.RM.index]
        del header[PrimaryKeysHeader.RM.index]
        new_data = [x for x in new_data if not None in x]
        pks_to_add = list()
        pks_to_remove = list()
        for row in new_data:
            if row not in self.original_pk_data:
                pks_to_add.append(row)
        for row in self.original_pk_data:
            if row not in new_data:
                pks_to_remove.append(row)
        # logging.debug("pks to add:{}".format(pks_to_add))
        # logging.debug("pks to_del:{}".format(pks_to_remove))
        for row in pks_to_add:
            table = row[header.index(PrimaryKeysHeader.TABLE.fullname)]
            field = row[header.index(PrimaryKeysHeader.FIELD.fullname)]
            self.dc.package.add_primary_key(table, field)
        for row in pks_to_remove:
            table = row[header.index(PrimaryKeysHeader.TABLE.fullname)]
            field = row[header.index(PrimaryKeysHeader.FIELD.fullname)]
            self.dc.package.rm_primary_key(table, field)
        # foreign keys
        new_data = deepcopy(self.fks_model.modelData())
        header = list(self.fks_model.header)
        for row in new_data:
            del row[ForeignKeysHeader.RM.index]
        del header[ForeignKeysHeader.RM.index]
        new_data = [x for x in new_data if not None in x]
        fks_to_add = list()
        fks_to_remove = list()
        for row in new_data:
            if row not in self.original_fk_data:
                fks_to_add.append(row)
        for row in self.original_fk_data:
            if row not in new_data:
                fks_to_remove.append(row)
        # logging.debug("fks to add:{}".format(fks_to_add))
        # logging.debug("fks to_del:{}".format(fks_to_remove))
        for row in fks_to_add:
            child_table = row[header.index(ForeignKeysHeader.CHILD_TABLE.fullname)]
            child_field = row[header.index(ForeignKeysHeader.CHILD_FIELD.fullname)]
            parent_table = row[header.index(ForeignKeysHeader.PARENT_TABLE.fullname)]
            parent_field = row[header.index(ForeignKeysHeader.PARENT_FIELD.fullname)]
            self.dc.package.add_foreign_key(child_table, child_field, parent_table, parent_field)
        for row in fks_to_remove:
            child_table = row[header.index(ForeignKeysHeader.CHILD_TABLE.fullname)]
            child_field = row[header.index(ForeignKeysHeader.CHILD_FIELD.fullname)]
            parent_table = row[header.index(ForeignKeysHeader.PARENT_TABLE.fullname)]
            parent_field = row[header.index(ForeignKeysHeader.PARENT_FIELD.fullname)]
            self.dc.package.rm_foreign_key(child_table, child_field, parent_table, parent_field)
        if pks_to_add or pks_to_remove or fks_to_add or fks_to_remove:
            self.dc.save_datapackage()
        self.close()

    @Slot(name='add_pk_clicked')
    def add_pk_clicked(self):
        """Creates new empty row in the Primary Keys model."""
        self.pks_model.insertRows(self.pks_model.rowCount(), 1)

    @Slot(name='add_fk_clicked')
    def add_fk_clicked(self):
        """Creates new empty row in the Foreign Keys model."""
        self.fks_model.insertRows(self.fks_model.rowCount(), 1)

    @Slot(name='rm_pks_clicked')
    def rm_pks_clicked(self):
        """Removes selected rows from Primary Keys model."""
        new_data = []
        for row in range(self.pks_model.rowCount()):
            index = self.pks_model.index(row, PrimaryKeysHeader.RM.index)
            if not self.pks_model.data(index):
                new_data.append(self.pks_model.rowData(row))
        self.pks_model.reset_model(new_data)

    @Slot(name='rm_fks_clicked')
    def rm_fks_clicked(self):
        """Removes selected rows from Foreign Keys model."""
        new_data = []
        for row in range(self.fks_model.rowCount()):
            index = self.fks_model.index(row, ForeignKeysHeader.RM.index)
            if not self.fks_model.data(index):
                new_data.append(self.fks_model.rowData(row))
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
