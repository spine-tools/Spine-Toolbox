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

:author: Manuel Marin <manuelma@kth.se>
:date:   13.5.2018
"""

from PySide2.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox, QAbstractItemView
from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QFont, QFontMetrics
from models import MinimalTableModel
from widgets.combobox_delegate import ComboBoxDelegate
import ui.add_object_classes
import ui.add_objects


class AddObjectClassesDialog(QDialog):
    def __init__(self, parent=None, object_class_query=None):
        super().__init__(parent)
        self.object_class_args_list = list()
        self.object_class_query = object_class_query
        self.ui = ui.add_object_classes.Ui_Dialog()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.model = MinimalTableModel(self)
        self.model.header = ['name', 'description']
        self.model.insertRows(0, 1)
        self.ui.tableView.setModel(self.model)
        # Add items to combobox
        insert_position_list = ['Insert at the top']
        insert_position_list.extend(['Insert after ' + item.name for item in self.object_class_query])
        self.ui.comboBox.addItems(insert_position_list)
        # Add actions to tool buttons
        self.ui.toolButton_insert_row.setDefaultAction(self.ui.actionInsert_row)
        self.ui.toolButton_remove_row.setDefaultAction(self.ui.actionRemove_row)
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.actionInsert_row.triggered.connect(self.insert_row)
        self.ui.actionRemove_row.triggered.connect(self.remove_row)

    @Slot(name="insert_row")
    def insert_row(self):
        current_row = self.ui.tableView.currentIndex().row()
        self.model.insertRows(current_row+1, 1)

    @Slot(name="remove_row")
    def remove_row(self):
        current_row = self.ui.tableView.currentIndex().row()
        self.model.removeRows(current_row, 1)

    def accept(self):
        index = self.ui.comboBox.currentIndex()
        if index == 0:
            display_order = self.object_class_query.first().display_order-1
        else:
            display_order = self.object_class_query.all()[index-1].display_order
        for i in range(self.model.rowCount()):
            row = self.model.rowData(i)
            if not row[0]:
                continue
            object_class_args = {
                'name': row[0],
                'description': row[1],
                'display_order': display_order
            }
            self.object_class_args_list.append(object_class_args)
        super().accept()


class AddObjectsDialog(QDialog):
    """A class to create custom forms with several line edits and comboboxes."""
    def __init__(self, parent=None, object_class_query=None, default_class_id=None):
        super().__init__(parent)
        self.object_args_list = list()
        self.object_class_query = object_class_query
        self.object_class_name_list = [item.name for item in object_class_query]
        # Get default class name. This happens when adding objects to specfic class via context menu
        self.default_class_name = None
        for object_class in self.object_class_query:
            if object_class.id == default_class_id:
                self.default_class_name = object_class.name
                break
        # Init ui
        self.ui = ui.add_objects.Ui_Dialog()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        # Override slot
        self.old_current_changed = self.ui.tableView.currentChanged
        self.ui.tableView.currentChanged = self.current_changed
        # Init model
        self.model = MinimalTableModel(self)
        self.model.header = ['class', 'name', 'description']
        self.model.insertRows(0, 1)
        self.model.setData(self.model.index(0, 0), self.default_class_name)
        self.model.setData(self.model.index(0, 0), self.object_class_name_list, Qt.UserRole)
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.setItemDelegateForColumn(0, ComboBoxDelegate(self))
        # Add actions to tool buttons
        self.ui.toolButton_insert_row.setDefaultAction(self.ui.actionInsert_row)
        self.ui.toolButton_remove_row.setDefaultAction(self.ui.actionRemove_row)
        self.connect_signals()

    def current_changed(self, current, previous):
        """Restore slot after view is initialized.
        This prevents automatically edit triggering as soon as dialog shows.
        """
        if current.model() == self.model:
            self.ui.tableView.setCurrentIndex(self.model.index(-1, -1))
            self.ui.tableView.currentChanged = self.old_current_changed

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.actionInsert_row.triggered.connect(self.insert_row)
        self.ui.actionRemove_row.triggered.connect(self.remove_row)
        self.ui.tableView.itemDelegateForColumn(0).closeEditor.connect(self.class_data_commited)

    @Slot(name="insert_row")
    def insert_row(self):
        current_row = self.ui.tableView.currentIndex().row()
        self.model.insertRows(current_row+1, 1)
        self.model.setData(self.model.index(current_row+1, 0), self.default_class_name)
        self.model.setData(self.model.index(current_row+1, 0), self.object_class_name_list, Qt.UserRole)

    @Slot(name="remove_row")
    def remove_row(self):
        current_row = self.ui.tableView.currentIndex().row()
        self.model.removeRows(current_row, 1)
        self.ui.tableView.setCurrentIndex(self.model.index(-1, -1))


    @Slot("QWidget", name='class_data_commited')
    def class_data_commited(self, editor):
        """Update 'class' field with data from combobox editor."""
        class_name = editor.currentText()
        row = editor.row
        column = editor.column
        index = self.model.index(row, column)
        self.model.setData(index, class_name, Qt.EditRole)

    def accept(self):
        for i in range(self.model.rowCount()):
            row = self.model.rowData(i)
            if not row[0] or not row[1]:
                continue
            class_id = None
            for object_class in self.object_class_query:
                if object_class.name == row[0]:
                    class_id = object_class.id
                    break
            if class_id is None:
                continue
            object_args = {
                'class_id': class_id,
                'name': row[1],
                'description': row[2]
            }
            self.object_args_list.append(object_args)
        super().accept()


class CustomQDialog(QDialog):
    """A class to create custom forms with several line edits and comboboxes."""
    def __init__(self, parent=None, title="", **kwargs):
        """Initialize class

        Args:
            parent (QWidget): the parent of this dialog, needed to center it properly
            title (str): window title
            kwargs (dict): keys to use when collecting the answer in output dict.
                Values are either placeholder texts or combobox lists.
        """
        super().__init__(parent)
        self.font = QFont("", 0)
        self.font_metric = QFontMetrics(self.font)
        self.input = dict()
        self.answer = dict()
        self.setWindowTitle(title)
        form = QFormLayout(self)
        for key,value in kwargs.items():
            if isinstance(value, str): # line edit
                input_ = QLineEdit(self)
                input_.setPlaceholderText(value)
                input_.setMinimumWidth(self.font_metric.width(value))
            elif isinstance(value, list): # combo box
                input_ = QComboBox(self)
                max_width = max(self.font_metric.width(x) for x in value if isinstance(x, str))
                input_.setMinimumWidth(max_width)
                input_.addItems(value)
            self.input[key] = input_
            form.addRow(input_)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)
        form.addRow(button_box)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    @Slot(name="save_and_accept")
    def save_and_accept(self):
        """Collect answer in output dict and accept"""
        for key,value in self.input.items():
            if isinstance(value, QLineEdit):
                self.answer[key] = value.text()
            elif isinstance(value, QComboBox):
                self.answer[key] = {
                    'text': value.currentText(),
                    'index': value.currentIndex()
                }
        self.accept()
