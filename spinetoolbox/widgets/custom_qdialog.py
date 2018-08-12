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

import logging
from PySide2.QtWidgets import QDialog, QFormLayout, QVBoxLayout, QPlainTextEdit, QLineEdit, \
    QDialogButtonBox, QComboBox, QHeaderView, QStatusBar, QStyle
from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QFont, QFontMetrics, QIcon, QPixmap
from config import STATUSBAR_SS
from models import MinimalTableModel
from widgets.combobox_delegate import ComboBoxDelegate
import ui.add_object_classes
import ui.add_objects
import ui.add_relationship_classes
import ui.add_relationships
import ui.add_parameters
import ui.add_parameter_values


class AddObjectClassesDialog(QDialog):
    """A dialog to query user's preferences for new object classes."""
    def __init__(self, parent, mapping):
        super().__init__(parent)
        self.object_class_list = mapping.object_class_list()
        self.object_class_args_list = list()
        self.ui = ui.add_object_classes.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.model = MinimalTableModel(self)
        self.model.header = ['name', 'description']
        self.insert_row()
        self.ui.tableView.setModel(self.model)
        self.resize_tableview()
        # Add items to combobox
        insert_position_list = ['Insert new classes at the top']
        insert_position_list.extend(["Insert new classes after '{}'".format(i.name) for i in self.object_class_list])
        self.ui.comboBox.addItems(insert_position_list)
        # Add actions to tool buttons
        self.ui.toolButton_insert_row.setDefaultAction(self.ui.actionInsert_row)
        self.ui.toolButton_remove_row.setDefaultAction(self.ui.actionRemove_row)
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.actionInsert_row.triggered.connect(self.insert_row)
        self.ui.actionRemove_row.triggered.connect(self.remove_row)

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        font_metric = QFontMetrics(QFont("", 0))
        header.resizeSection(0, 200)  # name
        header.resizeSection(1, 300)  # description
        table_width = font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(header.count()):
            table_width += self.ui.tableView.columnWidth(j)
        self.ui.tableView.setMinimumWidth(table_width)

    @Slot(name="insert_row")
    def insert_row(self):
        current_row = self.ui.tableView.currentIndex().row()
        self.model.insertRows(current_row+1, 1)

    @Slot(name="remove_row")
    def remove_row(self):
        current_row = self.ui.tableView.currentIndex().row()
        self.ui.tableView.setCurrentIndex(self.model.index(-1, -1))
        self.model.removeRows(current_row, 1)

    @Slot("QWidget", name="data_commited")
    def data_commited(self, editor):
        self.model.setData(editor.index, editor.text(), Qt.EditRole)

    def accept(self):
        index = self.ui.comboBox.currentIndex()
        if index == 0:
            display_order = self.object_class_list.first().display_order-1
        else:
            display_order = self.object_class_list.all()[index-1].display_order
        for i in range(self.model.rowCount()):
            name, description = self.model.rowData(i)
            if not name:
                continue
            object_class_args = {
                'name': name,
                'description': description,
                'display_order': display_order
            }
            self.object_class_args_list.append(object_class_args)
        super().accept()


class AddObjectsDialog(QDialog):
    """A dialog to query user's preferences for new objects."""
    def __init__(self, parent, mapping, class_id=None):
        super().__init__(parent)
        self.object_args_list = list()
        self.object_class_list = mapping.object_class_list()
        self.object_class_name_list = [item.name for item in self.object_class_list]
        default_class = mapping.single_object_class(class_id)
        self.default_class_name = default_class.name if default_class else None
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        # Init ui
        self.ui = ui.add_objects.Ui_Dialog()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # Override slot
        self.std_current_changed = self.ui.tableView.currentChanged
        self.ui.tableView.currentChanged = self.current_changed
        # Init model
        self.model = MinimalTableModel(self)
        self.model.header = ['class', 'name', 'description']
        self.insert_row()
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.setItemDelegateForColumn(0, ComboBoxDelegate(self))
        self.resize_tableview()
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
            self.ui.tableView.currentChanged = self.std_current_changed

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.actionInsert_row.triggered.connect(self.insert_row)
        self.ui.actionRemove_row.triggered.connect(self.remove_row)
        self.ui.tableView.itemDelegateForColumn(0).closeEditor.connect(self.class_data_commited)

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        font_metric = QFontMetrics(QFont("", 0))
        object_class_width = max([font_metric.width(x.name) for x in self.object_class_list], default=0)
        class_width = max(object_class_width, header.sectionSize(0))
        icon_width = qApp.style().pixelMetric(QStyle.PM_ListViewIconSize)
        header.resizeSection(0, icon_width + class_width)
        header.resizeSection(1, 200)
        header.resizeSection(2, 300)
        table_width = font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(header.count()):
            table_width += self.ui.tableView.columnWidth(j)
        self.ui.tableView.setMinimumWidth(table_width)

    @Slot(name="insert_row")
    def insert_row(self):
        row = self.ui.tableView.currentIndex().row()+1
        self.model.insertRows(row, 1)
        if self.default_class_name:
            self.model.setData(self.model.index(row, 0), self.default_class_name)
            self.model.setData(self.model.index(row, 0), self.object_icon, Qt.DecorationRole)
        self.model.setData(self.model.index(row, 0), self.object_class_name_list, Qt.UserRole)

    @Slot(name="remove_row")
    def remove_row(self):
        current_row = self.ui.tableView.currentIndex().row()
        self.ui.tableView.setCurrentIndex(self.model.index(-1, -1))
        self.model.removeRows(current_row, 1)

    @Slot("QWidget", name='class_data_commited')
    def class_data_commited(self, editor):
        """Update 'class' field with data from combobox editor."""
        class_name = editor.currentText()
        if not class_name:
            return
        row = editor.row
        column = editor.column
        index = self.model.index(row, column)
        self.model.setData(index, class_name, Qt.EditRole)
        self.model.setData(index, self.object_icon, Qt.DecorationRole)

    def accept(self):
        for i in range(self.model.rowCount()):
            class_name, name, description = self.model.rowData(i)
            if not class_name or not name:
                continue
            class_id = self.object_class_list.filter_by(name=class_name).one().id
            object_args = {
                'class_id': class_id,
                'name': name,
                'description': description
            }
            self.object_args_list.append(object_args)
        super().accept()


class AddRelationshipClassesDialog(QDialog):
    """A dialog to query user's preferences for new relationship classes."""
    def __init__(self, parent, mapping, parent_relationship_class_id=None, parent_object_class_id=None):
        super().__init__(parent)
        self.relationship_class_args_list = list()
        self.object_class_list = mapping.object_class_list()
        self.relationship_class_list = mapping.any_relationship_class_list()
        self.parent_class_name_list = [item.name for item in self.object_class_list]
        self.parent_class_name_list.extend([item.name for item in self.relationship_class_list])
        self.child_object_class_name_list = [item.name for item in self.object_class_list]
        # Icon initialization
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        self.relationship_icon = QIcon(QPixmap(":/icons/relationship_icon.png"))
        # Default parent name
        self.default_parent_class_name = None
        if parent_object_class_id:
            parent_object_class = mapping.single_object_class(id=parent_object_class_id)
            if parent_object_class:
                self.default_parent_class_name = parent_object_class.name
                self.default_parent_class_icon = self.object_icon
        elif parent_relationship_class_id:
            parent_relationship_class = mapping.single_relationship_class(id=parent_relationship_class_id)
            if parent_relationship_class:
                self.default_parent_class_name = parent_relationship_class.name
                self.default_parent_class_icon = self.relationship_icon
        # Init ui
        self.ui = ui.add_relationship_classes.Ui_Dialog()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # Override slot
        self.std_current_changed = self.ui.tableView.currentChanged
        self.ui.tableView.currentChanged = self.current_changed
        # Init model
        self.model = MinimalTableModel(self)
        self.model.header = ['parent class', 'child class', 'name']
        self.insert_row()
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.setItemDelegateForColumn(0, ComboBoxDelegate(self))
        self.ui.tableView.setItemDelegateForColumn(1, ComboBoxDelegate(self))
        self.resize_tableview()
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
            self.ui.tableView.currentChanged = self.std_current_changed

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.actionInsert_row.triggered.connect(self.insert_row)
        self.ui.actionRemove_row.triggered.connect(self.remove_row)
        self.ui.tableView.itemDelegateForColumn(0).closeEditor.connect(self.class_data_commited)
        self.ui.tableView.itemDelegateForColumn(1).closeEditor.connect(self.class_data_commited)

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        font_metric = QFontMetrics(QFont("", 0))
        relationship_class_width = max([font_metric.width(x.name) for x in self.relationship_class_list], default=0)
        object_class_width = max([font_metric.width(x.name) for x in self.object_class_list], default=0)
        parent_class_width = max(relationship_class_width, object_class_width, header.sectionSize(0))
        child_class_width = max(object_class_width, header.sectionSize(1))
        name_width = max(parent_class_width + child_class_width, header.sectionSize(2))
        icon_width = qApp.style().pixelMetric(QStyle.PM_ListViewIconSize)
        header.resizeSection(0, icon_width + parent_class_width)
        header.resizeSection(1, icon_width + child_class_width)
        header.resizeSection(2, name_width)
        table_width = font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(header.count()):
            table_width += self.ui.tableView.columnWidth(j)
        self.ui.tableView.setMinimumWidth(table_width)

    @Slot(name="insert_row")
    def insert_row(self):
        row = self.ui.tableView.currentIndex().row()+1
        self.model.insertRows(row, 1)
        if self.default_parent_class_name:
            self.model.setData(self.model.index(row, 0), self.default_parent_class_name)
            self.model.setData(self.model.index(row, 0), self.default_parent_class_icon, Qt.DecorationRole)
        self.model.setData(self.model.index(row, 0), self.parent_class_name_list, Qt.UserRole)
        self.model.setData(self.model.index(row, 1), self.child_object_class_name_list, Qt.UserRole)

    @Slot(name="remove_row")
    def remove_row(self):
        current_row = self.ui.tableView.currentIndex().row()
        self.ui.tableView.setCurrentIndex(self.model.index(-1, -1))
        self.model.removeRows(current_row, 1)

    @Slot("QWidget", name='class_data_commited')
    def class_data_commited(self, editor):
        """Update 'parent class' or 'child_class' field with data from combobox editor."""
        class_name = editor.currentText()
        if not class_name:
            return
        row = editor.row
        column = editor.column
        index = self.model.index(row, column)
        self.model.setData(index, class_name, Qt.EditRole)
        object_class = self.object_class_list.filter_by(name=class_name).one_or_none()
        if object_class:
            class_icon = self.object_icon
        else:
            class_icon = self.relationship_icon
        self.model.setData(index, class_icon, Qt.DecorationRole)
        # Compose relationship class name automatically
        parent_class_name = self.model.data(index.sibling(row, 0), Qt.DisplayRole)
        child_class_name = self.model.data(index.sibling(row, 1), Qt.DisplayRole)
        try:
            relationship_class_name = parent_class_name + '_' + child_class_name
            self.model.setData(index.sibling(row, 2), relationship_class_name, Qt.EditRole)
        except TypeError:
            pass

    def accept(self):
        for i in range(self.model.rowCount()):
            row = self.model.rowData(i)
            if any([True for i in row if not i]):
                continue
            parent_class_name, child_class_name, name = row
            parent_object_class = self.object_class_list.\
                filter_by(name=parent_class_name).one_or_none()
            parent_relationship_class = self.relationship_class_list.\
                filter_by(name=parent_class_name).one_or_none()
            if parent_object_class is None and parent_relationship_class is None:
                continue
            parent_object_class_id = parent_object_class.id if parent_object_class else None
            parent_relationship_class_id = parent_relationship_class.id if parent_relationship_class else None
            child_object_class_id = self.object_class_list.filter_by(name=child_class_name).one().id
            relationship_class_args = {
                'parent_object_class_id': parent_object_class_id,
                'parent_relationship_class_id': parent_relationship_class_id,
                'child_object_class_id': child_object_class_id,
                'name': name
            }
            self.relationship_class_args_list.append(relationship_class_args)
        super().accept()


class AddRelationshipsDialog(QDialog):
    """A dialog to query user's preferences for new relationships."""
    def __init__(self, parent, mapping, class_id=None, parent_relationship_id=None,
            parent_object_id=None, child_object_id=None
        ):
        super().__init__(parent)
        self.relationship_args_list = list()
        self.object_class_list = mapping.object_class_list()
        self.relationship_class_list = mapping.any_relationship_class_list()
        self.object_list = mapping.object_list()
        self.relationship_list = mapping.relationship_list()
        self.class_name_list = [item.name for item in self.relationship_class_list]
        # Icon initialization
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        self.relationship_icon = QIcon(QPixmap(":/icons/relationship_icon.png"))
        # Default parent names
        self.default_class_name = None
        self.default_parent_name = None
        self.default_child_name = None
        if class_id:
            relationship_class = mapping.single_relationship_class(id=class_id)
            if relationship_class:
                self.default_class_name = relationship_class.name
                self.default_class_icon = self.relationship_icon
        if parent_object_id:
            parent_object = mapping.single_object(id=parent_object_id)
            if parent_object:
                self.default_parent_name = parent_object.name
                self.default_parent_icon = self.object_icon
        elif parent_relationship_id:
            parent_relationship = mapping.single_relationship(id=parent_relationship_id)
            if parent_relationship:
                self.default_parent_name = parent_relationship.name
                self.default_parent_icon = self.relationship_icon
        elif child_object_id:
            child_object = mapping.single_object(id=child_object_id)
            if child_object:
                self.default_child_name = child_object.name
                self.default_child_icon = self.object_icon
        # Init ui
        self.ui = ui.add_relationships.Ui_Dialog()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # Override slot
        self.std_current_changed = self.ui.tableView.currentChanged
        self.ui.tableView.currentChanged = self.current_changed
        self.std_edit = self.ui.tableView.edit
        self.ui.tableView.edit = self.edit
        # Init model
        self.model = MinimalTableModel(self)
        self.model.header = ['class', 'parent', 'child', 'name']
        self.insert_row()
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.setItemDelegateForColumn(0, ComboBoxDelegate(self))
        self.ui.tableView.setItemDelegateForColumn(1, ComboBoxDelegate(self))
        self.ui.tableView.setItemDelegateForColumn(2, ComboBoxDelegate(self))
        self.resize_tableview()
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
            self.ui.tableView.currentChanged = self.std_current_changed

    def edit(self, index, trigger, event):
        if index.column() in [1, 2] and index.data(Qt.UserRole) is None:
            self.statusbar.showMessage("Please select relationship class first.", 5000)
            return False
        return self.std_edit(index, trigger, event)

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.actionInsert_row.triggered.connect(self.insert_row)
        self.ui.actionRemove_row.triggered.connect(self.remove_row)
        self.ui.tableView.itemDelegateForColumn(0).closeEditor.connect(self.class_data_commited)
        self.ui.tableView.itemDelegateForColumn(1).closeEditor.connect(self.data_commited)
        self.ui.tableView.itemDelegateForColumn(2).closeEditor.connect(self.data_commited)

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        font_metric = QFontMetrics(QFont("", 0))
        relationship_class_width = max([font_metric.width(x.name) for x in self.relationship_class_list], default=0)
        object_width = max([font_metric.width(x.name) for x in self.object_list], default=0)
        relationship_width = max([font_metric.width(x.name) for x in self.relationship_list], default=0)
        class_width = max(relationship_class_width, header.sectionSize(0))
        parent_width = max(object_width, relationship_width, header.sectionSize(1))
        child_width = max(object_width, header.sectionSize(2))
        name_width = max(parent_width + child_width, header.sectionSize(3))
        icon_width = qApp.style().pixelMetric(QStyle.PM_ListViewIconSize)
        header.resizeSection(0, icon_width + class_width)
        header.resizeSection(1, icon_width + parent_width)
        header.resizeSection(2, icon_width + child_width)
        header.resizeSection(3, name_width)
        table_width = font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(header.count()):
            table_width += self.ui.tableView.columnWidth(j)
        self.ui.tableView.setMinimumWidth(table_width)

    @Slot(name="insert_row")
    def insert_row(self):
        row = self.ui.tableView.currentIndex().row()+1
        self.model.insertRows(row, 1)
        if self.default_class_name:
            self.model.setData(self.model.index(row, 0), self.default_class_name)
            self.model.setData(self.model.index(row, 0), self.default_class_icon, Qt.DecorationRole)
            self.update_parent_and_child_combos(self.default_class_name, row)
        if self.default_parent_name:
            self.model.setData(self.model.index(row, 1), self.default_parent_name)
            self.model.setData(self.model.index(row, 1), self.default_parent_icon, Qt.DecorationRole)
        if self.default_child_name:
            self.model.setData(self.model.index(row, 2), self.default_child_name)
            self.model.setData(self.model.index(row, 2), self.default_child_icon, Qt.DecorationRole)
        self.model.setData(self.model.index(row, 0), self.class_name_list, Qt.UserRole)

    @Slot(name="remove_row")
    def remove_row(self):
        current_row = self.ui.tableView.currentIndex().row()
        self.ui.tableView.setCurrentIndex(self.model.index(-1, -1))
        self.model.removeRows(current_row, 1)

    @Slot("QWidget", name='class_data_commited')
    def class_data_commited(self, editor):
        """Update 'class' field with data from combobox editor
        and update comboboxes for 'parent' and 'child' fields accordingly.
        """
        class_name = editor.currentText()
        if not class_name:
            return
        row = editor.row
        column = editor.column
        index = self.model.index(row, column)
        self.model.setData(index, class_name, Qt.EditRole)
        self.model.setData(index, self.relationship_icon, Qt.DecorationRole)
        self.model.setData(index.sibling(row, 1), None, Qt.EditRole)
        self.model.setData(index.sibling(row, 1), None, Qt.DecorationRole)
        self.model.setData(index.sibling(row, 2), None, Qt.EditRole)
        self.model.setData(index.sibling(row, 2), None, Qt.DecorationRole)
        self.update_parent_and_child_combos(class_name, row)

    def update_parent_and_child_combos(self, name, row):
        """Update options available in comboboxes for parent and child.

        Args:
            name (str): The name of a relationship class.
            row (int): The row in the model.
        """
        relationship_class = self.relationship_class_list.filter_by(name=name).one_or_none()
        msg = ""
        if not relationship_class:
            logging.debug("Couldn't find relationship class '{}'. This is odd.".format(name))
            return
        if relationship_class.parent_object_class_id is not None:
            class_id = relationship_class.parent_object_class_id
            parent_name_list = [item.name for item in self.object_list.filter_by(class_id=class_id)]
            if not parent_name_list:
                class_name = self.object_class_list.filter_by(id=class_id).one().name
                msg += "Class '{}' does not have any objects. ".format(class_name)
        elif relationship_class.parent_relationship_class_id is not None:
            class_id = relationship_class.parent_relationship_class_id
            parent_name_list = [item.name for item in self.relationship_list.filter_by(class_id=class_id)]
            if not parent_name_list:
                class_name = self.relationship_class_list.filter_by(id=class_id).one().name
                msg += "Class '{}' does not have any relationships. ".format(class_name)
        class_id = relationship_class.child_object_class_id
        child_name_list = [item.name for item in self.object_list.filter_by(class_id=class_id)]
        if not child_name_list:
            class_name = self.object_class_list.filter_by(id=class_id).one().name
            msg += "Class '{}' does not have any objects. ".format(class_name)
        self.model.setData(self.model.index(row, 1), parent_name_list, Qt.UserRole)
        self.model.setData(self.model.index(row, 2), child_name_list, Qt.UserRole)
        self.statusbar.showMessage(msg, 5000)

    @Slot("QWidget", name='data_commited')
    def data_commited(self, editor):
        """Update 'parent' or 'child' field with data from combobox editor."""
        name = editor.currentText()
        if not name:
            return
        row = editor.row
        column = editor.column
        index = self.model.index(row, column)
        self.model.setData(index, name, Qt.EditRole)
        if column == 1:
            parent_object = self.object_list.filter_by(name=name).one_or_none()
            if parent_object:
                parent_icon = self.object_icon
            else:
                parent_icon = self.relationship_icon
            self.model.setData(index, parent_icon, Qt.DecorationRole)
        elif column == 2:
            self.model.setData(index, self.object_icon, Qt.DecorationRole)
        # Compose relationship name automatically
        parent_name = self.model.data(index.sibling(row, 1), Qt.DisplayRole)
        child_name = self.model.data(index.sibling(row, 2), Qt.DisplayRole)
        try:
            relationship_name = parent_name + '_' + child_name
            self.model.setData(index.sibling(row, 3), relationship_name, Qt.EditRole)
        except TypeError:
            pass

    def accept(self):
        for i in range(self.model.rowCount()):
            row = self.model.rowData(i)
            if any([True for i in row if not i]):
                continue
            class_name, parent_name, child_name, name = row
            class_id = self.relationship_class_list.filter_by(name=class_name).one().id
            parent_object = self.object_list.filter_by(name=parent_name).one_or_none()
            parent_relationship = self.relationship_list.filter_by(name=parent_name).one_or_none()
            if parent_object is None and parent_relationship is None:
                continue
            parent_object_id = parent_object.id if parent_object else None
            parent_relationship_id = parent_relationship.id if parent_relationship else None
            child_object_id = self.object_list.filter_by(name=child_name).one().id
            relationship_args = {
                'class_id': class_id,
                'parent_object_id': parent_object_id,
                'parent_relationship_id': parent_relationship_id,
                'child_object_id': child_object_id,
                'name': name
            }
            self.relationship_args_list.append(relationship_args)
        super().accept()


class AddParametersDialog(QDialog):
    """A dialog to query user's preferences for new parameters."""
    def __init__(self, parent, mapping, object_class_id=None, relationship_class_id=None):
        super().__init__(parent)
        self.parameter_args_list = list()
        self.object_class_list = mapping.object_class_list()
        self.relationship_class_list = mapping.relationship_class_list()
        self.class_name_list = [item.name for item in self.object_class_list]
        self.class_name_list.extend([item.name for item in self.relationship_class_list])
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        self.relationship_icon = QIcon(QPixmap(":/icons/relationship_icon.png"))
        # Default parent name
        self.default_class_name = None
        if object_class_id:
            object_class = mapping.single_object_class(id=object_class_id)
            if object_class:
                self.default_class_name = object_class.name
                self.default_class_icon = self.object_icon
        elif relationship_class_id:
            relationship_class = mapping.single_relationship_class(id=relationship_class_id)
            if relationship_class:
                self.default_class_name = relationship_class.name
                self.default_class_icon = self.relationship_icon
        # Init ui
        self.ui = ui.add_parameters.Ui_Dialog()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # Override slot
        self.std_current_changed = self.ui.tableView.currentChanged
        self.ui.tableView.currentChanged = self.current_changed
        # Init model
        self.model = MinimalTableModel(self)
        self.model.header = ['class', 'name']
        self.insert_row()
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.setItemDelegateForColumn(0, ComboBoxDelegate(self))
        self.resize_tableview()
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
            self.ui.tableView.currentChanged = self.std_current_changed

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.actionInsert_row.triggered.connect(self.insert_row)
        self.ui.actionRemove_row.triggered.connect(self.remove_row)
        self.ui.tableView.itemDelegateForColumn(0).closeEditor.connect(self.class_data_commited)

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        font_metric = QFontMetrics(QFont("", 0))
        object_class_width = max([font_metric.width(x.name) for x in self.object_class_list], default=0)
        relationship_class_width = max([font_metric.width(x.name) for x in self.relationship_class_list], default=0)
        class_width = max(object_class_width, relationship_class_width, header.sectionSize(0))
        icon_width = qApp.style().pixelMetric(QStyle.PM_ListViewIconSize)
        header.resizeSection(0, icon_width + class_width)
        header.resizeSection(1, 200)  # name
        table_width = font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(header.count()):
            table_width += self.ui.tableView.columnWidth(j)
        self.ui.tableView.setMinimumWidth(table_width)

    @Slot(name="insert_row")
    def insert_row(self):
        row = self.ui.tableView.currentIndex().row()+1
        self.model.insertRows(row, 1)
        if self.default_class_name:
            self.model.setData(self.model.index(row, 0), self.default_class_name)
            self.model.setData(self.model.index(row, 0), self.default_class_icon, Qt.DecorationRole)
        self.model.setData(self.model.index(row, 0), self.class_name_list, Qt.UserRole)

    @Slot(name="remove_row")
    def remove_row(self):
        current_row = self.ui.tableView.currentIndex().row()
        self.ui.tableView.setCurrentIndex(self.model.index(-1, -1))
        self.model.removeRows(current_row, 1)

    @Slot("QWidget", name='class_data_commited')
    def class_data_commited(self, editor):
        """Update 'class' field with data from combobox editor."""
        class_name = editor.currentText()
        if not class_name:
            return
        row = editor.row
        column = editor.column
        index = self.model.index(row, column)
        self.model.setData(index, class_name, Qt.EditRole)
        object_class = self.object_class_list.filter_by(name=class_name).one_or_none()
        if object_class:
            class_icon = self.object_icon
        else:
            class_icon = self.relationship_icon
        self.model.setData(index, class_icon, Qt.DecorationRole)

    def accept(self):
        for i in range(self.model.rowCount()):
            row = self.model.rowData(i)
            if any([True for i in row if not i]):
                continue
            class_name, name = row
            object_class = self.object_class_list.filter_by(name=class_name).one_or_none()
            relationship_class = self.relationship_class_list.filter_by(name=class_name).one_or_none()
            if object_class is None and relationship_class is None:
                continue
            object_class_id = object_class.id if object_class else None
            relationship_class_id = relationship_class.id if relationship_class else None
            parameter_args = {
                'object_class_id': object_class_id,
                'relationship_class_id': relationship_class_id,
                'name': name
            }
            self.parameter_args_list.append(parameter_args)
        super().accept()


class AddParameterValuesDialog(QDialog):
    """A dialog to query user's preferences for new parameter values."""
    # TODO: Filter out parameters that already have a value.
    def __init__(self, parent, mapping, object_class_id=None, relationship_class_id=None,
            object_id=None, relationship_id=None
        ):
        super().__init__(parent)
        self.parameter_value_args_list = list()
        self.object_class_list = mapping.object_class_list()
        self.relationship_class_list = mapping.relationship_class_list()
        self.object_list = mapping.object_list()
        self.relationship_list = mapping.relationship_list()
        self.parameter_list = mapping.parameter_list()
        self.class_name_list = [item.name for item in self.object_class_list]
        self.class_name_list.extend([item.name for item in self.relationship_class_list])
        # Icon initialization
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        self.relationship_icon = QIcon(QPixmap(":/icons/relationship_icon.png"))
        # Default names
        self.default_class_name = None
        self.default_entity_name = None
        if object_class_id:
            object_class = mapping.single_object_class(id=object_class_id)
            if object_class:
                self.default_class_name = object_class.name
                self.default_class_icon = self.object_icon
        elif relationship_class_id:
            relationship_class = mapping.single_relationship_class(id=relationship_class_id)
            if relationship_class:
                self.default_class_name = relationship_class.name
                self.default_class_icon = self.relationship_icon
        if object_id:
            object_ = mapping.single_object(id=object_id)
            if object_:
                self.default_entity_name = object_.name
                self.default_entity_icon = self.object_icon
        elif relationship_id:
            relationship = mapping.single_relationship(id=relationship_id)
            if relationship:
                self.default_entity_name = relationship.name
                self.default_entity_icon = self.relationship_icon
        # Init ui
        self.ui = ui.add_parameter_values.Ui_Dialog()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        # Override slot
        self.std_current_changed = self.ui.tableView.currentChanged
        self.ui.tableView.currentChanged = self.current_changed
        self.std_edit = self.ui.tableView.edit
        self.ui.tableView.edit = self.edit
        # Init model
        self.model = MinimalTableModel(self)
        self.model.header = ['class', 'entity', 'parameter', 'value', 'json']
        self.insert_row()
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.setItemDelegateForColumn(0, ComboBoxDelegate(self))
        self.ui.tableView.setItemDelegateForColumn(1, ComboBoxDelegate(self))
        self.ui.tableView.setItemDelegateForColumn(2, ComboBoxDelegate(self))
        self.resize_tableview()
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
            self.ui.tableView.currentChanged = self.std_current_changed

    def edit(self, index, trigger, event):
        if index.column() in (1, 2) and index.data(Qt.UserRole) is None:
            self.statusbar.showMessage("Please select class first.", 5000)
            return False
        return self.std_edit(index, trigger, event)

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.actionInsert_row.triggered.connect(self.insert_row)
        self.ui.actionRemove_row.triggered.connect(self.remove_row)
        self.ui.tableView.itemDelegateForColumn(0).closeEditor.connect(self.class_data_commited)
        self.ui.tableView.itemDelegateForColumn(1).closeEditor.connect(self.entity_data_commited)
        self.ui.tableView.itemDelegateForColumn(2).closeEditor.connect(self.parameter_data_commited)

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        font_metric = QFontMetrics(QFont("", 0))
        object_class_width = max([font_metric.width(x.name) for x in self.object_class_list], default=0)
        relationship_class_width = max([font_metric.width(x.name) for x in self.relationship_class_list], default=0)
        object_width = max([font_metric.width(x.name) for x in self.object_list], default=0)
        relationship_width = max([font_metric.width(x.name) for x in self.relationship_list], default=0)
        parameter_width = max([font_metric.width(x.name) for x in self.parameter_list], default=0)
        class_width = max(object_class_width, relationship_class_width, header.sectionSize(0))
        entity_width = max(object_width, relationship_width, header.sectionSize(1))
        parameter_width = max(parameter_width, header.sectionSize(2))
        icon_width = qApp.style().pixelMetric(QStyle.PM_ListViewIconSize)
        header.resizeSection(0, icon_width + class_width)
        header.resizeSection(1, icon_width + entity_width)
        header.resizeSection(2, icon_width + parameter_width)
        header.resizeSection(3, 80)  # value
        header.resizeSection(4, 80)  # json
        table_width = font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(header.count()):
            table_width += self.ui.tableView.columnWidth(j)
        self.ui.tableView.setMinimumWidth(table_width)

    @Slot(name="insert_row")
    def insert_row(self):
        row = self.ui.tableView.currentIndex().row()+1
        self.model.insertRows(row, 1)
        if self.default_class_name:
            self.model.setData(self.model.index(row, 0), self.default_class_name)
            self.model.setData(self.model.index(row, 0), self.default_class_icon, Qt.DecorationRole)
            self.update_entity_combo(self.default_class_name, row)
            self.update_parameter_combo(self.default_class_name, row)
        if self.default_entity_name:
            self.model.setData(self.model.index(row, 1), self.default_entity_name)
            self.model.setData(self.model.index(row, 1), self.default_entity_icon, Qt.DecorationRole)
        self.model.setData(self.model.index(row, 0), self.class_name_list, Qt.UserRole)

    @Slot(name="remove_row")
    def remove_row(self):
        current_row = self.ui.tableView.currentIndex().row()
        self.ui.tableView.setCurrentIndex(self.model.index(-1, -1))
        self.model.removeRows(current_row, 1)

    @Slot("QWidget", name='class_data_commited')
    def class_data_commited(self, editor):
        """Update 'class' field with data from combobox editor
        and update comboboxes for 'entity' field accordingly.
        """
        class_name = editor.currentText()
        if not class_name:
            return
        row = editor.row
        column = editor.column
        index = self.model.index(row, column)
        self.model.setData(index, class_name, Qt.EditRole)
        object_class = self.object_class_list.filter_by(name=class_name).one_or_none()
        if object_class:
            class_icon = self.object_icon
        else:
            class_icon = self.relationship_icon
        self.model.setData(index, class_icon, Qt.DecorationRole)
        self.model.setData(index.sibling(row, 1), None, Qt.EditRole)
        self.model.setData(index.sibling(row, 1), None, Qt.DecorationRole)
        self.model.setData(index.sibling(row, 2), None, Qt.EditRole)
        self.update_entity_combo(class_name, row)
        self.update_parameter_combo(class_name, row)

    def update_entity_combo(self, name, row):
        """Update options available in combobox for entity.

        Args:
            name (str): The name of a class.
            row (int): The row in the model.
        """
        msg = self.statusbar.currentMessage()
        object_class = self.object_class_list.filter_by(name=name).one_or_none()
        relationship_class = self.relationship_class_list.filter_by(name=name).one_or_none()
        if object_class:
            entity_name_list = [i.name for i in self.object_list.filter_by(class_id=object_class.id)]
            if not entity_name_list:
                msg += "Class '{}' does not have any objects. ".format(name)
        elif relationship_class:
            entity_name_list = [i.name for i in self.relationship_list.filter_by(class_id=relationship_class.id)]
            if not entity_name_list:
                msg += "Class '{}' does not have any relationships. ".format(name)
        else:
            logging.debug("Couldn't find class '{}'. This is odd.".format(name))
            return
        self.model.setData(self.model.index(row, 1), entity_name_list, Qt.UserRole)
        self.statusbar.showMessage(msg, 5000)

    def update_parameter_combo(self, name, row):
        """Update options available in combobox for entity.

        Args:
            name (str): The name of a class.
            row (int): The row in the model.
        """
        msg = self.statusbar.currentMessage()
        object_class = self.object_class_list.filter_by(name=name).one_or_none()
        relationship_class = self.relationship_class_list.filter_by(name=name).one_or_none()
        if object_class:
            class_id = object_class.id
            parameter_name_list = [i.name for i in self.parameter_list.filter_by(object_class_id=class_id)]
        elif relationship_class:
            class_id = relationship_class.id
            parameter_name_list = [i.name for i in self.parameter_list.filter_by(relationship_class_id=class_id)]
        else:
            logging.debug("Couldn't find class '{}'. This is odd.".format(name))
            return
        if not parameter_name_list:
            msg += "Class '{}' does not have any parameters. ".format(name)
        self.model.setData(self.model.index(row, 2), parameter_name_list, Qt.UserRole)
        self.statusbar.showMessage(msg, 5000)

    @Slot("QWidget", name='entity_data_commited')
    def entity_data_commited(self, editor):
        """Update 'entity' field with data from combobox editor."""
        entity_name = editor.currentText()
        if not entity_name:
            return
        row = editor.row
        column = editor.column
        index = self.model.index(row, column)
        self.model.setData(index, entity_name, Qt.EditRole)
        object_ = self.object_list.filter_by(name=entity_name).one_or_none()
        if object_:
            entity_icon = self.object_icon
        else:
            entity_icon = self.relationship_icon
        self.model.setData(index, entity_icon, Qt.DecorationRole)

    @Slot("QWidget", name='parameter_data_commited')
    def parameter_data_commited(self, editor):
        """Update 'parameter' field with data from combobox editor."""
        parameter_name = editor.currentText()
        if not parameter_name:
            return
        row = editor.row
        column = editor.column
        index = self.model.index(row, column)
        self.model.setData(index, parameter_name, Qt.EditRole)

    def accept(self):
        for i in range(self.model.rowCount()):
            class_name, entity_name, parameter_name, value, json = self.model.rowData(i)
            if not entity_name or not parameter_name:
                continue
            if not value and not json:
                continue
            object_ = self.object_list.filter_by(name=entity_name).one_or_none()
            relationship = self.relationship_list.filter_by(name=entity_name).one_or_none()
            if object_ is None and relationship is None:
                continue
            object_id = object_.id if object_ else None
            relationship_id = relationship.id if relationship else None
            parameter_id = self.parameter_list.filter_by(name=parameter_name).one().id
            parameter_value_args = {
                'object_id': object_id,
                'relationship_id': relationship_id,
                'parameter_id': parameter_id,
                'value': value,
                'json': json
            }
            self.parameter_value_args_list.append(parameter_value_args)
        super().accept()


class CommitDialog(QDialog):
    """A dialog to query user's preferences for new parameter values."""
    def __init__(self, parent, database):
        """Initialize class

        Args:
            parent (QWidget): the parent of this dialog, needed to center it properly.
            database (str): The database name.
        """
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
