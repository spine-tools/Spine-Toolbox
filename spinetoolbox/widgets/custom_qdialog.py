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
from PySide2.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox, \
    QHeaderView, QStatusBar, QStyle
from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QFont, QFontMetrics, QIcon, QPixmap
from config import STATUSBAR_SS
from models import MinimalTableModel
from widgets.combobox_delegate import ComboBoxDelegate
import ui.add_object_classes
import ui.add_objects
import ui.add_relationship_classes
import ui.add_relationships


class AddObjectClassesDialog(QDialog):
    """A dialog to query user's preferences for new object classes."""
    def __init__(self, parent=None, object_class_query=None):
        super().__init__(parent)
        self.object_class_args_list = list()
        self.object_class_query = object_class_query
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
        insert_position_list.extend(["Insert new classes after '{}'".format(i.name) for i in self.object_class_query])
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
        font_metric = QFontMetrics(QFont("", 0))
        self.ui.tableView.horizontalHeader().resizeSection(0, 200)
        self.ui.tableView.horizontalHeader().resizeSection(1, 300)
        new_width = font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(self.ui.tableView.horizontalHeader().count()):
            new_width += self.ui.tableView.columnWidth(j)
        self.ui.tableView.setMinimumWidth(new_width)

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
    """A dialog to query user's preferences for new objects."""
    def __init__(self, parent=None, object_class_query=None, class_name=None):
        super().__init__(parent)
        self.object_args_list = list()
        self.object_class_query = object_class_query
        self.object_class_name_list = [item.name for item in object_class_query]
        self.default_class_name = class_name
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
        font_metric = QFontMetrics(QFont("", 0))
        object_class_width = max(font_metric.width(x.name) for x in self.object_class_query)
        icon_width = qApp.style().pixelMetric(QStyle.PM_ListViewIconSize)
        self.ui.tableView.horizontalHeader().resizeSection(0, icon_width + object_class_width)
        self.ui.tableView.horizontalHeader().resizeSection(1, 200)
        self.ui.tableView.horizontalHeader().resizeSection(2, 300)
        new_width = font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(self.ui.tableView.horizontalHeader().count()):
            new_width += self.ui.tableView.columnWidth(j)
        self.ui.tableView.setMinimumWidth(new_width)

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
            row = self.model.rowData(i)
            if any([True for i in row if not i]):
                continue
            class_id = self.object_class_query.filter_by(name=row[0]).one().id
            object_args = {
                'class_id': class_id,
                'name': row[1],
                'description': row[2]
            }
            self.object_args_list.append(object_args)
        super().accept()


class AddRelationshipClassesDialog(QDialog):
    """A dialog to query user's preferences for new relationship classes."""
    def __init__(self, parent=None, object_class_query=None, relationship_class_query=None,
            parent_class_name=None):
        super().__init__(parent)
        self.relationship_class_args_list = list()
        self.object_class_query = object_class_query
        self.relationship_class_query = relationship_class_query
        self.parent_class_name_list = [item.name for item in object_class_query]
        self.parent_class_name_list.extend([item.name for item in relationship_class_query])
        self.child_object_class_name_list = [item.name for item in object_class_query]
        self.default_parent_class_name = parent_class_name
        # Icon initialization
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        self.relationship_icon = QIcon(QPixmap(":/icons/relationship_icon.png"))
        parent_object_class = self.object_class_query.filter_by(name=parent_class_name).one_or_none()
        if parent_object_class:
            self.default_parent_class_icon = self.object_icon
        else:
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
        font_metric = QFontMetrics(QFont("", 0))
        relationship_class_width = max(font_metric.width(x.name) for x in self.relationship_class_query)
        object_class_width = max(font_metric.width(x.name) for x in self.object_class_query)
        icon_width = qApp.style().pixelMetric(QStyle.PM_ListViewIconSize)
        max_width = max(relationship_class_width, object_class_width)
        self.ui.tableView.horizontalHeader().resizeSection(0, icon_width + max_width)
        self.ui.tableView.horizontalHeader().resizeSection(1, icon_width + object_class_width)
        self.ui.tableView.horizontalHeader().resizeSection(2, max_width + object_class_width)
        new_width = font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(self.ui.tableView.horizontalHeader().count()):
            new_width += self.ui.tableView.columnWidth(j)
        self.ui.tableView.setMinimumWidth(new_width)

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
        object_class = self.object_class_query.filter_by(name=class_name).one_or_none()
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
            parent_object_class = self.object_class_query.\
                filter_by(name=row[0]).one_or_none()
            parent_relationship_class = self.relationship_class_query.\
                filter_by(name=row[0]).one_or_none()
            if parent_object_class is None and parent_relationship_class is None:
                continue
            parent_object_class_id = parent_object_class.id if parent_object_class else None
            parent_relationship_class_id = parent_relationship_class.id if parent_relationship_class else None
            child_object_class_id = self.object_class_query.\
                filter_by(name=row[1]).one().id
            relationship_class_args = {
                'parent_object_class_id': parent_object_class_id,
                'parent_relationship_class_id': parent_relationship_class_id,
                'child_object_class_id': child_object_class_id,
                'name': row[2]
            }
            self.relationship_class_args_list.append(relationship_class_args)
        super().accept()


class AddRelationshipsDialog(QDialog):
    """A dialog to query user's preferences for new relationships."""
    def __init__(self, parent=None, relationship_class_query=None, object_query=None, relationship_query=None,
            class_name=None, parent_name=None, child_name=None
        ):
        super().__init__(parent)
        self.relationship_args_list = list()
        self.relationship_class_query = relationship_class_query
        self.object_query = object_query
        self.relationship_query = relationship_query
        self.class_name_list = [item.name for item in relationship_class_query]
        self.default_class_name = class_name
        self.default_parent_name = parent_name
        self.default_child_name = child_name
        # Icon initialization
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        self.relationship_icon = QIcon(QPixmap(":/icons/relationship_icon.png"))
        self.default_class_icon = self.relationship_icon
        parent_object = self.object_query.filter_by(name=parent_name).one_or_none()
        if parent_object:
            self.default_parent_icon = self.object_icon
        else:
            self.default_parent_icon = self.relationship_icon
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
        print(index)
        if index.column() in [1, 2] and not index.data(Qt.UserRole):
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
        font_metric = QFontMetrics(QFont("", 0))
        relationship_class_width = max(font_metric.width(x.name) for x in self.relationship_class_query)
        object_width = max(font_metric.width(x.name) for x in self.object_query)
        relationship_width = max(font_metric.width(x.name) for x in self.relationship_query)
        icon_width = qApp.style().pixelMetric(QStyle.PM_ListViewIconSize)
        self.ui.tableView.horizontalHeader().resizeSection(0, icon_width + relationship_class_width)
        self.ui.tableView.horizontalHeader().resizeSection(1, icon_width + max(object_width, relationship_width))
        self.ui.tableView.horizontalHeader().resizeSection(2, icon_width + object_width)
        self.ui.tableView.horizontalHeader().resizeSection(3, max(object_width, relationship_width) + object_width)
        new_width = font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(self.ui.tableView.horizontalHeader().count()):
            new_width += self.ui.tableView.columnWidth(j)
        self.ui.tableView.setMinimumWidth(new_width)

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
        relationship_class = self.relationship_class_query.filter_by(name=name).one_or_none()
        if not relationship_class:
            logging.debug("Couldn't find relationship class '{}'. This is odd.".format(name))
            return
        if relationship_class.parent_object_class_id is not None:
            class_id = relationship_class.parent_object_class_id
            parent_name_list = [item.name for item in self.object_query.filter_by(class_id=class_id)]
        elif relationship_class.parent_relationship_class_id is not None:
            class_id = relationship_class.parent_relationship_class_id
            parent_name_list = [item.name for item in self.relationship_query.filter_by(class_id=class_id)]
        class_id = relationship_class.child_object_class_id
        child_name_list = [item.name for item in self.object_query.filter_by(class_id=class_id)]
        self.model.setData(self.model.index(row, 1), parent_name_list, Qt.UserRole)
        self.model.setData(self.model.index(row, 2), child_name_list, Qt.UserRole)

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
            parent_object = self.object_query.filter_by(name=name).one_or_none()
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
            class_id = self.relationship_class_query.filter_by(name=row[0]).one().id
            parent_object = self.object_query.filter_by(name=row[1]).one_or_none()
            parent_relationship = self.relationship_query.filter_by(name=row[1]).one_or_none()
            if parent_object is None and parent_relationship is None:
                continue
            parent_object_id = parent_object.id if parent_object else None
            parent_relationship_id = parent_relationship.id if parent_relationship else None
            child_object_id = self.object_query.filter_by(name=row[2]).one().id
            relationship_args = {
                'class_id': class_id,
                'parent_object_id': parent_object_id,
                'parent_relationship_id': parent_relationship_id,
                'child_object_id': child_object_id,
                'name': row[3]
            }
            self.relationship_args_list.append(relationship_args)
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
