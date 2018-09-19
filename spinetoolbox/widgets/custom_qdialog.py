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
Various QDialogs to add items to Database in DataStoreForm,
and a QDialog that can be programmatically populated with many options.
Originally intended to be used within DataStoreForm

TODO: CustomQDialog has a syntax error, so it does not even work.
NOTE: Where is this syntax error? We better fix it, since CustomQDialog is inherited by all other AddStuffDialogs
:author: M. Marin (KTH)
:date:   13.5.2018
"""

import logging
from copy import deepcopy
from PySide2.QtWidgets import QDialog, QFormLayout, QVBoxLayout, QPlainTextEdit, QLineEdit, \
    QDialogButtonBox, QComboBox, QHeaderView, QStatusBar, QStyle
from PySide2.QtCore import Signal, Slot, Qt
from PySide2.QtGui import QFont, QFontMetrics, QIcon, QPixmap
from config import STATUSBAR_SS
from models import MinimalTableModel
from widgets.custom_delegates import AddObjectsDelegate, AddRelationshipClassesDelegate, AddRelationshipsDelegate, \
    LineEditDelegate
import ui.add_object_classes
import ui.add_objects
import ui.add_relationship_classes
import ui.add_relationships
import ui.add_parameters
import ui.add_parameter_values


class CustomQDialog(QDialog):
    """A dialog with options to insert and remove rows from a tableview.

    Attributes:
        parent (DataStoreForm): data store widget
    """
    confirmed = Signal("QVariant", name="confirmed")

    def __init__(self, parent):
        super().__init__(parent)
        self.ui = None
        self.model = MinimalTableModel(self)
        self.model.can_grow = True
        self.args_list = list()
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        self.relationship_icon = QIcon(QPixmap(":/icons/relationship_icon.png"))
        self.icon_width = qApp.style().pixelMetric(QStyle.PM_ListViewIconSize)
        self.font_metric = QFontMetrics(QFont("", 0))
        self.setAttribute(Qt.WA_DeleteOnClose)

    def setup_ui(self, ui_dialog):
        self.ui = ui_dialog
        self.ui.setupUi(self)
        self.ui.toolButton_insert_row.setDefaultAction(self.ui.actionInsert_row)
        self.ui.toolButton_remove_rows.setDefaultAction(self.ui.actionRemove_rows)
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.actionInsert_row.triggered.connect(self.insert_row)
        self.ui.actionRemove_rows.triggered.connect(self.remove_rows)
        self.ui.tableView.itemDelegate().commitData.connect(self.data_committed)
        self.model.dataChanged.connect(self.model_data_changed)

    def resize_tableview(self):
        table_width = self.font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(self.ui.tableView.horizontalHeader().count()-1):
            table_width += self.ui.tableView.horizontalHeader().sectionSize(j)
        section = self.ui.tableView.horizontalHeader().count()-1
        table_width += min(250, self.ui.tableView.horizontalHeader().sectionSize(section))
        self.ui.tableView.setMinimumWidth(table_width)

    @Slot(name="insert_row")
    def insert_row(self, row=False):
        if row is False:
            row = self.ui.tableView.currentIndex().row()+1
        self.model.insertRows(row, 1)

    @Slot(name="remove_rows")
    def remove_rows(self):
        selection = self.ui.tableView.selectionModel().selection()
        row_set = set()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_set.update(range(top, bottom+1))
        for row in reversed(list(row_set)):
            self.model.removeRows(row, 1)

    @Slot("QWidget", name='data_committed')
    def data_committed(self, editor):
        """Update 'object x' field with data from combobox editor."""
        data = editor.text()
        if not data:
            return
        index = editor.index()
        self.model.setData(index, data, Qt.EditRole)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="model_data_changed")
    def model_data_changed(self, top_left, bottom_right, roles):
        pass

    def accept(self):
        """Emit confirmed signal"""
        self.confirmed.emit(self.args_list)
        super().accept()


class AddObjectClassesDialog(CustomQDialog):
    """A dialog to query user's preferences for new object classes.

    Attributes:
        parent (DataStoreForm): data store widget
        db_mngr (Databasedb_mngr): database handle from `spinedatabase_api`
    """
    def __init__(self, parent, db_mngr):
        super().__init__(parent)
        self.object_class_list = [x for x in db_mngr.object_class_list()]
        self.setup_ui(ui.add_object_classes.Ui_Dialog())
        self.ui.tableView.setItemDelegate(LineEditDelegate(parent))
        self.model.set_horizontal_header_labels(['object class name', 'description'])
        self.model.clear()
        # Add items to combobox
        insert_position_list = ['Insert new classes at the top']
        insert_position_list.extend(
            ["Insert new classes after '{}'".format(i.name) for i in self.object_class_list])
        self.ui.comboBox.addItems(insert_position_list)
        self.connect_signals()
        self.insert_row()
        self.resize_tableview()

    def resize_tableview(self):
        self.ui.tableView.horizontalHeader().resizeSection(0, 200)  # name
        self.ui.tableView.horizontalHeader().resizeSection(1, 300)  # description
        super().resize_tableview()

    def accept(self):
        index = self.ui.comboBox.currentIndex()
        if index == 0:
            display_order = self.object_class_list[0].display_order-1
        else:
            display_order = self.object_class_list[index-1].display_order
        for i in range(self.model.rowCount()):
            name, description = self.model.row_data(i)
            if not name:
                continue
            object_class_args = {
                'name': name,
                'description': description,
                'display_order': display_order
            }
            self.args_list.append(object_class_args)
        super().accept()


class AddObjectsDialog(CustomQDialog):
    """A dialog to query user's preferences for new objects.

    Attributes:
        parent (DataStoreForm): data store widget
        db_mngr (Databasedb_mngr): database handle from `spinedatabase_api`
        class_id (int): default object class id
    """
    def __init__(self, parent, db_mngr, class_id=None):
        super().__init__(parent)
        self.db_mngr = db_mngr
        default_class = db_mngr.single_object_class(id=class_id).one_or_none()
        self.default_class_name = default_class.name if default_class else None
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        self.model.set_horizontal_header_labels(['object class name', 'object name', 'description'])
        self.setup_ui(ui.add_objects.Ui_Dialog())
        self.ui.tableView.setItemDelegate(AddObjectsDelegate(parent))
        self.connect_signals()
        self.insert_row()
        self.resize_tableview()

    def connect_signals(self):
        """Connect signals to slots."""
        self.model.rowsInserted.connect(self.setup_new_row)
        super().connect_signals()

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        object_class_width = max(
            [self.font_metric.width(x.name) for x in self.db_mngr.object_class_list()], default=0)
        class_width = max(object_class_width, header.sectionSize(0))
        header.resizeSection(0, self.icon_width + class_width)
        header.resizeSection(1, 200)
        header.resizeSection(2, 300)
        super().resize_tableview()

    @Slot("QModelIndex", "int", "int", name="setup_new_row")
    def setup_new_row(self, parent, first, last):
        if self.default_class_name:
            self.model.setData(self.model.index(first, 0, parent), self.default_class_name)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="model_data_changed")
    def model_data_changed(self, top_left, bottom_right, roles):
        if roles[0] != Qt.EditRole:
            return
        h = self.model.horizontal_header_labels().index
        if top_left.column() == h('object class name'):
            self.model.setData(top_left, self.object_icon, Qt.DecorationRole)

    def accept(self):
        for i in range(self.model.rowCount()):
            class_name, name, description = self.model.row_data(i)
            if not class_name or not name:
                continue
            class_ = self.db_mngr.single_object_class(name=class_name).one_or_none()
            if not class_:
                continue
            object_args = {
                'class_id': class_.id,
                'name': name,
                'description': description
            }
            self.args_list.append(object_args)
        super().accept()


class AddRelationshipClassesDialog(CustomQDialog):
    """A dialog to query user's preferences for new relationship classes.

    Attributes:
        parent (DataStoreForm): data store widget
        db_mngr (Databasedb_mngr): database handle from `spinedatabase_api`
        object_class_one_id (int): default object class id to put in dimension '1'
    """
    def __init__(self, parent, db_mngr, object_class_one_id=None):
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.number_of_dimensions = 2
        self.object_class_one_name = None
        if object_class_one_id:
            object_class_one = db_mngr.single_object_class(id=object_class_one_id).one_or_none()
            if object_class_one:
                self.object_class_one_name = object_class_one.name
        self.model.set_horizontal_header_labels(
            ['object class 1 name', 'object class 2 name', 'relationship class name'])
        self.setup_ui(ui.add_relationship_classes.Ui_Dialog())
        self.ui.tableView.setItemDelegate(AddRelationshipClassesDelegate(parent))
        self.connect_signals()
        self.insert_row()
        self.resize_tableview()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.spinBox.valueChanged.connect(self.insert_or_remove_column)
        self.model.rowsInserted.connect(self.setup_new_row)
        super().connect_signals()

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        object_class_width = max([self.font_metric.width(x.name) for x in self.db_mngr.object_class_list()], default=0)
        for column in range(self.number_of_dimensions):
            header.resizeSection(column, self.icon_width + object_class_width)
            header.resizeSection(column, self.icon_width + object_class_width)
        name_width = max(self.number_of_dimensions * object_class_width, header.sectionSize(self.number_of_dimensions))
        header.resizeSection(self.number_of_dimensions, name_width)

    @Slot("int", name="insert_or_remove_column")
    def insert_or_remove_column(self, i):
        self.ui.spinBox.setEnabled(False)
        if i > self.number_of_dimensions:
            self.insert_column()
        elif i < self.number_of_dimensions:
            self.remove_column()
        self.ui.spinBox.setEnabled(True)
        for row in range(self.model.rowCount()):
            self.compose_relationship_class_name(row)

    def insert_column(self):
        column = self.number_of_dimensions
        self.number_of_dimensions += 1
        self.model.header.insert(column, {})
        column_name = "object class {} name".format(self.number_of_dimensions)
        self.model.setHeaderData(column, Qt.Horizontal, column_name, Qt.EditRole)
        self.model.insertColumns(column, 1)
        self.ui.tableView.resizeColumnToContents(column)

    def remove_column(self):
        self.number_of_dimensions -= 1
        column = self.number_of_dimensions
        self.model.header.pop(column)
        self.model.removeColumns(column, 1)

    @Slot("QModelIndex", "int", "int", name="setup_new_row")
    def setup_new_row(self, parent, first, last):
        if self.object_class_one_name:
            self.model.setData(self.model.index(first, 0), self.object_class_one_name)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="model_data_changed")
    def model_data_changed(self, top_left, bottom_right, roles):
        if roles[0] != Qt.EditRole:
            return
        h = self.model.horizontal_header_labels().index
        if top_left.column() != h('relationship class name'):
            self.model.setData(top_left, self.object_icon, Qt.DecorationRole)
            self.compose_relationship_class_name(top_left.row())

    def compose_relationship_class_name(self, row):
        """Compose relationship class name automatically."""
        object_class_name_list = list()
        name_column = self.model.columnCount() - 1
        for column in range(name_column):  # Leave 'name' column outside
            index = self.model.index(row, column)
            object_class_name = self.model.data(index, Qt.DisplayRole)
            if object_class_name:
                object_class_name_list.append(object_class_name)
        relationship_class_name = "__".join(object_class_name_list)
        self.model.setData(index.sibling(row, name_column), relationship_class_name, Qt.EditRole)

    def accept(self):
        name_column = self.model.columnCount() - 1
        for i in range(self.model.rowCount()):
            row = self.model.row_data(i)
            relationship_class_name = row[name_column]
            if not relationship_class_name:
                continue
            object_class_id_list = list()
            for column in range(name_column):  # Leave 'name' column outside
                object_class_name = row[column]
                if not object_class_name:
                    continue
                object_class = self.db_mngr.single_object_class(name=object_class_name).one_or_none()
                if not object_class:
                    continue
                object_class_id_list.append(object_class.id)
            if len(object_class_id_list) < 2:
                continue
            wide_relationship_class_args = {
                'name': relationship_class_name,
                'object_class_id_list': object_class_id_list
            }
            self.args_list.append(wide_relationship_class_args)
        super().accept()


class AddRelationshipsDialog(CustomQDialog):
    """A dialog to query user's preferences for new relationships.

    Attributes:
        parent (DataStoreForm): data store widget
        db_mngr (Databasedb_mngr): database handle from `spinedatabase_api`
        relationship_class_id (int): default relationship class id
        object_id (int): default object id
        object_class_id (int): default object class id
    """
    def __init__(self, parent, db_mngr, relationship_class_id=None, object_id=None, object_class_id=None):
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.relationship_class_list = \
            [x for x in db_mngr.wide_relationship_class_list(object_class_id=object_class_id)]
        self.relationship_class = None
        self.relationship_class_id = relationship_class_id
        self.object_id = object_id
        self.object_class_id = object_class_id
        self.default_object_column = None
        self.default_object_name = None
        self.object_class_id_list = None
        self.set_default_object_name()
        self.setup_ui(ui.add_relationships.Ui_Dialog())
        self.ui.toolButton_insert_row.setEnabled(False)
        self.ui.toolButton_remove_rows.setEnabled(False)
        self.ui.tableView.setItemDelegate(AddRelationshipsDelegate(parent))
        self.ui.tableView.itemDelegate().commitData.connect(self.data_committed)
        self.init_relationship_class()
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        self.connect_signals()
        self.reset_model()

    def init_relationship_class(self):
        """Populate combobox and initialize relationship class if needed."""
        relationship_class_name_list = [x.name for x in self.relationship_class_list]
        self.ui.comboBox_relationship_class.addItems(relationship_class_name_list)
        self.ui.comboBox_relationship_class.setCurrentIndex(-1)
        self.relationship_class = self.db_mngr.\
            single_wide_relationship_class(id=self.relationship_class_id).one_or_none()
        if not self.relationship_class:
            return
        try:
            combo_index = relationship_class_name_list.index(self.relationship_class.name)
            self.ui.comboBox_relationship_class.setCurrentIndex(combo_index)
        except ValueError:
            pass

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.comboBox_relationship_class.currentIndexChanged.connect(self.call_reset_model)
        self.model.rowsInserted.connect(self.setup_new_row)
        super().connect_signals()

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        font_metric = QFontMetrics(QFont("", 0))
        icon_width = qApp.style().pixelMetric(QStyle.PM_ListViewIconSize)
        name_width = 0
        for section, object_class_id in enumerate(self.object_class_id_list):
            object_list = self.db_mngr.object_list(class_id=object_class_id)
            object_width = max([font_metric.width(x.name) for x in object_list], default=0)
            section_width = max(icon_width + object_width, header.sectionSize(section))
            header.resizeSection(section, section_width)
            name_width += object_width
        section = header.count()-1
        section_width = max(name_width, header.sectionSize(section))
        header.resizeSection(section, section_width)
        super().resize_tableview()

    @Slot("int", name='call_reset_model')
    def call_reset_model(self, index):
        """Called when relationship class's combobox's index changes.
        Update relationship_class attribute accordingly and reset model."""
        self.relationship_class = self.relationship_class_list[index]
        self.reset_model()

    def reset_model(self):
        """Setup model according to current relationship class selected in combobox
        (or given as input).
        """
        if not self.relationship_class:
            return
        object_class_id_list = self.relationship_class.object_class_id_list
        self.object_class_id_list = [int(x) for x in object_class_id_list.split(',')]
        header = list()
        for object_class_id in self.object_class_id_list:
            object_class = self.db_mngr.single_object_class(id=object_class_id).one_or_none()
            if not object_class:
                logging.debug("Couldn't find object class, probably a bug.")
                return
            header.append("{} name".format(object_class.name))
        header.append('relationship name')
        self.model.set_horizontal_header_labels(header)
        self.model.clear()
        self.reset_default_object_column()
        self.insert_row()
        self.resize_tableview()
        self.ui.toolButton_insert_row.setEnabled(True)
        self.ui.toolButton_remove_rows.setEnabled(True)

    def set_default_object_name(self):
        if not self.object_id:
            return
        object_ = self.db_mngr.single_object(id=self.object_id).one_or_none()
        if not object_:
            return
        self.default_object_name = object_.name

    def reset_default_object_column(self):
        if not self.default_object_name:
            return
        if not self.relationship_class or not self.object_class_id:
            return
        try:
            object_class_id_list = self.relationship_class.object_class_id_list
            self.default_object_column = [int(x) for x in object_class_id_list.split(',')].index(self.object_class_id)
        except ValueError:
            pass

    @Slot("QModelIndex", "int", "int", name="setup_new_row")
    def setup_new_row(self, parent, first, last):
        if self.default_object_name and self.default_object_column is not None:
            index = self.model.index(first, self.default_object_column)
            self.model.setData(index, self.default_object_name, Qt.EditRole)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="model_data_changed")
    def model_data_changed(self, top_left, bottom_right, roles):
        if roles[0] != Qt.EditRole:
            return
        h = self.model.horizontal_header_labels().index
        if top_left.column() != h('relationship name'):
            self.model.setData(top_left, self.object_icon, Qt.DecorationRole)
            self.compose_relationship_name(top_left.row())

    def compose_relationship_name(self, row):
        """Compose relationship name automatically."""
        object_name_list = list()
        name_column = self.model.columnCount() - 1
        for column in range(name_column):  # Leave 'name' column outside
            index = self.model.index(row, column)
            object_name = self.model.data(index, Qt.DisplayRole)
            if object_name:
                object_name_list.append(object_name)
        relationship_name = "__".join(object_name_list)
        self.model.setData(index.sibling(row, name_column), relationship_name, Qt.EditRole)

    def accept(self):
        name_column = self.model.columnCount() - 1
        for i in range(self.model.rowCount()):
            row = self.model.row_data(i)
            relationship_name = row[name_column]
            if not relationship_name:
                continue
            object_id_list = list()
            for column in range(name_column):  # Leave 'name' column outside
                object_name = row[column]
                if not object_name:
                    continue
                object_ = self.db_mngr.single_object(name=object_name).one_or_none()
                if not object_:
                    continue
                object_id_list.append(object_.id)
            if len(object_id_list) < 2:
                continue
            wide_relationship_args = {
                'name': relationship_name,
                'object_id_list': object_id_list,
                'class_id': self.relationship_class.id
            }
            self.args_list.append(wide_relationship_args)
        super().accept()


class CommitDialog(QDialog):
    """A dialog to query user's preferences for new parameter values.

    Attributes:
        parent (DataStoreForm): data store widget
        database (str): database name
    """
    def __init__(self, parent, database):
        """Initialize class"""
        super().__init__(parent)
        self.commit_msg = None
        self.setWindowTitle('Commit changes to {}'.format(database))
        form = QVBoxLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(4, 4, 4, 4)
        self.commit_msg_edit = QPlainTextEdit(self)
        self.commit_msg_edit.setPlaceholderText('Commit message')
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box = QDialogButtonBox()
        button_box.addButton(QDialogButtonBox.Cancel)
        button_box.addButton('Commit', QDialogButtonBox.AcceptRole)
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)
        inner_layout.addWidget(self.commit_msg_edit)
        inner_layout.addWidget(button_box)
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        form.addLayout(inner_layout)
        form.addWidget(self.statusbar)
        self.setAttribute(Qt.WA_DeleteOnClose)

    @Slot(name="save_and_accept")
    def save_and_accept(self):
        """Check if everything is ok and accept"""
        self.commit_msg = self.commit_msg_edit.toPlainText()
        if not self.commit_msg:
            self.statusbar.showMessage("Please enter a commit message.", 3000)
            return
        self.accept()
