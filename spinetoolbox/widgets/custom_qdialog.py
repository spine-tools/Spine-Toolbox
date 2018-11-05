######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes for custom QDialogs to add and edit database items.

TODO: AddItemsDialog has a syntax error, so it does not even work.
NOTE: Where is this syntax error? We better fix it, since AddItemsDialog is inherited by all other AddStuffDialogs
:author: M. Marin (KTH)
:date:   13.5.2018
"""

import logging
from copy import deepcopy
from PySide2.QtWidgets import QDialog, QFormLayout, QVBoxLayout, QPlainTextEdit, QLineEdit, \
    QDialogButtonBox, QComboBox, QHeaderView, QStatusBar, QStyle, QAction, QApplication
from PySide2.QtCore import Signal, Slot, Qt
from PySide2.QtGui import QFont, QFontMetrics, QIcon, QPixmap
from spinedatabase_api import SpineDBAPIError, SpineIntegrityError
from config import STATUSBAR_SS
from models import MinimalTableModel
from widgets.custom_delegates import AddObjectsDelegate, AddRelationshipClassesDelegate, AddRelationshipsDelegate, \
    LineEditDelegate
import ui.add_object_classes
import ui.add_objects
import ui.add_relationship_classes
import ui.add_relationships
import ui.edit_data_items


class AddItemsDialog(QDialog):
    """A dialog to query user's preferences for new object classes.

    Attributes:
        parent (TreeViewForm): data store widget
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self.ui = None
        self.model = MinimalTableModel(self, can_grow=True, has_empty_row=True)
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        self.relationship_icon = QIcon(QPixmap(":/icons/relationship_icon.png"))
        self.icon_width = qApp.style().pixelMetric(QStyle.PM_ListViewIconSize)
        self.font_metric = QFontMetrics(QFont("", 0))
        self.setAttribute(Qt.WA_DeleteOnClose)

    def setup_ui(self, ui_dialog):
        self.ui = ui_dialog
        self.ui.setupUi(self)
        self.ui.toolButton_remove_rows.setDefaultAction(self.ui.actionRemove_rows)
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.actionRemove_rows.triggered.connect(self.remove_rows)
        self.ui.tableView.itemDelegate().commit_model_data.connect(self.data_committed)
        self.model.dataChanged.connect(self.model_data_changed)

    def resize_tableview(self):
        table_width = self.font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(self.ui.tableView.horizontalHeader().count() - 1):
            table_width += self.ui.tableView.horizontalHeader().sectionSize(j)
        section = self.ui.tableView.horizontalHeader().count() - 1
        table_width += min(250, self.ui.tableView.horizontalHeader().sectionSize(section))
        self.ui.tableView.setMinimumWidth(table_width)

    @Slot(name="remove_rows")
    def remove_rows(self):
        selection = self.ui.tableView.selectionModel().selection()
        row_set = set()
        while not selection.isEmpty():
            current = selection.takeFirst()
            top = current.top()
            bottom = current.bottom()
            row_set.update(range(top, bottom + 1))
        for row in reversed(list(row_set)):
            self.model.removeRows(row, 1)

    @Slot("QModelIndex", "QVariant", name='data_committed')
    def data_committed(self, index, data):
        """Update 'object x' field with data from combobox editor."""
        if data is None:
            return
        self.model.setData(index, data, Qt.EditRole)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="model_data_changed")
    def model_data_changed(self, top_left, bottom_right, roles):
        """Reimplement this method in subclasses to handle changes in model data."""
        pass


class AddObjectClassesDialog(AddItemsDialog):
    """A dialog to query user's preferences for new object classes.

    Attributes:
        parent (TreeViewForm): data store widget
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.object_class_list = self._parent.db_map.object_class_list()
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
        self.resize_tableview()

    def resize_tableview(self):
        self.ui.tableView.horizontalHeader().resizeSection(0, 150)  # name
        self.ui.tableView.horizontalHeader().resizeSection(1, 200)  # description
        super().resize_tableview()

    def accept(self):
        """Collect info from dialog and try to add items."""
        kwargs_list = list()
        index = self.ui.comboBox.currentIndex()
        if index == 0:
            try:
                display_order = self.object_class_list.first().display_order - 1
            except AttributeError:
                display_order = 1
        else:
            display_order = self.object_class_list.all()[index - 1].display_order + 1
        for i in range(self.model.rowCount()):
            name, description = self.model.row_data(i)
            if not name:
                continue
            kwargs = {
                'name': name,
                'description': description,
                'display_order': display_order
            }
            kwargs_list.append(kwargs)
        try:
            object_classes = self._parent.db_map.add_object_classes(*kwargs_list)
            self._parent.add_object_classes(object_classes)
            super().accept()
        except SpineIntegrityError as e:
            self._parent.msg_error.emit(e.msg)
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class AddObjectsDialog(AddItemsDialog):
    """A dialog to query user's preferences for new objects.

    Attributes:
        parent (TreeViewForm): data store widget
        class_id (int): default object class id
    """
    def __init__(self, parent, class_id=None):
        super().__init__(parent)
        self.setup_ui(ui.add_objects.Ui_Dialog())
        self.ui.tableView.setItemDelegate(AddObjectsDelegate(self.ui.tableView, parent.db_map))
        self.connect_signals()
        default_class = self._parent.db_map.single_object_class(id=class_id).one_or_none()
        self.default_class_name = default_class.name if default_class else None
        self.model.set_horizontal_header_labels(['object class name', 'object name', 'description'])
        self.model.set_row_defaults([self.default_class_name], [Qt.DisplayRole, Qt.EditRole])
        self.model.set_row_defaults([self.object_icon], [Qt.DecorationRole])
        self.model.clear()
        self.resize_tableview()

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        object_class_width = max(
            [self.font_metric.width(x.name) for x in self._parent.db_map.object_class_list()], default=0)
        class_width = max(object_class_width, header.sectionSize(0))
        header.resizeSection(0, self.icon_width + class_width)
        header.resizeSection(1, 150)
        header.resizeSection(2, 200)
        super().resize_tableview()

    def accept(self):
        """Collect info from dialog and try to add items."""
        kwargs_list = list()
        for i in range(self.model.rowCount()):
            class_name, name, description = self.model.row_data(i)
            if not class_name or not name:
                continue
            class_ = self._parent.db_map.single_object_class(name=class_name).one_or_none()
            if not class_:
                continue
            kwargs = {
                'class_id': class_.id,
                'name': name,
                'description': description
            }
            kwargs_list.append(kwargs)
        try:
            objects = self._parent.db_map.add_objects(*kwargs_list)
            self._parent.add_objects(objects)
            super().accept()
        except SpineIntegrityError as e:
            self._parent.msg_error.emit(e.msg)
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class AddRelationshipClassesDialog(AddItemsDialog):
    """A dialog to query user's preferences for new relationship classes.

    Attributes:
        parent (TreeViewForm): data store widget
        object_class_one_id (int): default object class id to put in dimension '1'
    """
    def __init__(self, parent, object_class_one_id=None):
        super().__init__(parent)
        self.setup_ui(ui.add_relationship_classes.Ui_Dialog())
        self.ui.tableView.setItemDelegate(AddRelationshipClassesDelegate(self.ui.tableView, parent.db_map))
        self.connect_signals()
        self.number_of_dimensions = 2
        self.object_class_one_name = None
        if object_class_one_id:
            object_class_one = self._parent.db_map.single_object_class(id=object_class_one_id).one_or_none()
            if object_class_one:
                self.object_class_one_name = object_class_one.name
        self.model.set_horizontal_header_labels(
            ['object class 1 name', 'object class 2 name', 'relationship class name'])
        self.model.set_row_defaults([self.object_class_one_name], [Qt.DisplayRole, Qt.EditRole])
        self.model.set_row_defaults([self.object_icon] * self.number_of_dimensions, [Qt.DecorationRole])
        self.model.clear()
        self.resize_tableview()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.spinBox.valueChanged.connect(self.insert_or_remove_column)
        super().connect_signals()

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        object_class_width = max(
            [self.font_metric.width(x.name) for x in self._parent.db_map.object_class_list()], default=0)
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

    def insert_column(self):
        column = self.number_of_dimensions
        self.number_of_dimensions += 1
        column_name = "object class {} name".format(self.number_of_dimensions)
        self.model.insert_horizontal_header_labels(column, [column_name])
        self.model.set_row_defaults([self.object_icon] * self.number_of_dimensions, [Qt.DecorationRole])
        self.model.insertColumns(column, 1)
        self.ui.tableView.resizeColumnToContents(column)

    def remove_column(self):
        self.number_of_dimensions -= 1
        column = self.number_of_dimensions
        self.model.header.pop(column)
        self.model.row_defaults.pop(column)
        self.model.removeColumns(column, 1)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="model_data_changed")
    def model_data_changed(self, top_left, bottom_right, roles):
        if Qt.EditRole not in roles:
            return
        relationship_class_name_column = self.model.horizontal_header_labels().index('relationship class name')
        top = top_left.row()
        left = top_left.column()
        bottom = bottom_right.row()
        right = bottom_right.column()
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                if column == relationship_class_name_column:
                    continue
                index = self.model.index(row, column)
                self.compose_relationship_class_name(row)

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
        """Collect info from dialog and try to add items."""
        wide_kwargs_list = list()
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
                object_class = self._parent.db_map.single_object_class(name=object_class_name).one_or_none()
                if not object_class:
                    continue
                object_class_id_list.append(object_class.id)
            if len(object_class_id_list) < 2:
                continue
            wide_kwargs = {
                'name': relationship_class_name,
                'object_class_id_list': object_class_id_list
            }
            wide_kwargs_list.append(wide_kwargs)
        try:
            wide_relationship_classes = self._parent.db_map.add_wide_relationship_classes(*wide_kwargs_list)
            self._parent.add_relationship_classes(wide_relationship_classes)
            super().accept()
        except SpineIntegrityError as e:
            self._parent.msg_error.emit(e.msg)
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class AddRelationshipsDialog(AddItemsDialog):
    """A dialog to query user's preferences for new relationships.

    Attributes:
        parent (TreeViewForm): data store widget
        relationship_class_id (int): default relationship class id
        object_id (int): default object id
        object_class_id (int): default object class id
    """
    def __init__(self, parent, relationship_class_id=None, object_id=None, object_class_id=None):
        super().__init__(parent)
        self.relationship_class_list = \
            [x for x in self._parent.db_map.wide_relationship_class_list(object_class_id=object_class_id)]
        self.relationship_class = None
        self.relationship_class_id = relationship_class_id
        self.object_id = object_id
        self.object_class_id = object_class_id
        self.default_object_column = None
        self.default_object_name = None
        self.set_default_object_name()
        self.setup_ui(ui.add_relationships.Ui_Dialog())
        self.ui.toolButton_remove_rows.setEnabled(False)
        self.ui.tableView.setItemDelegate(AddRelationshipsDelegate(self.ui.tableView, parent.db_map))
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
        self.relationship_class = self._parent.db_map.\
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
        super().connect_signals()

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        font_metric = QFontMetrics(QFont("", 0))
        icon_width = qApp.style().pixelMetric(QStyle.PM_ListViewIconSize)
        name_width = 0
        object_class_id_list = [int(x) for x in self.relationship_class.object_class_id_list.split(',')]
        for section, object_class_id in enumerate(object_class_id_list):
            object_list = self._parent.db_map.object_list(class_id=object_class_id)
            object_width = max([font_metric.width(x.name) for x in object_list], default=0)
            section_width = max(icon_width + object_width, header.sectionSize(section))
            header.resizeSection(section, section_width)
            name_width += object_width
        section = header.count() - 1
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
        object_class_name_list = self.relationship_class.object_class_name_list.split(',')
        header = [*[x + " name" for x in object_class_name_list], 'relationship name']
        self.model.set_horizontal_header_labels(header)
        self.reset_default_object_column()
        if self.default_object_name and self.default_object_column is not None:
            defaults = [None for i in range(len(header) - 1)]
            defaults[self.default_object_column] = self.default_object_name
            self.model.set_row_defaults(defaults, [Qt.DisplayRole, Qt.EditRole])
        self.model.set_row_defaults([self.object_icon] * (len(header) - 1), [Qt.DecorationRole])
        self.model.clear()
        self.resize_tableview()
        self.ui.toolButton_remove_rows.setEnabled(True)

    def set_default_object_name(self):
        if not self.object_id:
            return
        object_ = self._parent.db_map.single_object(id=self.object_id).one_or_none()
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

    @Slot("QModelIndex", "QModelIndex", "QVector", name="model_data_changed")
    def model_data_changed(self, top_left, bottom_right, roles):
        if Qt.EditRole not in roles:
            return
        relationship_name_column = self.model.horizontal_header_labels().index('relationship name')
        top = top_left.row()
        left = top_left.column()
        bottom = bottom_right.row()
        right = bottom_right.column()
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                if column == relationship_name_column:
                    continue
                index = self.model.index(row, column)
                self.compose_relationship_name(row)

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
        """Collect info from dialog and try to add items."""
        wide_kwargs_list = list()
        name_column = self.model.columnCount() - 1
        for i in range(self.model.rowCount()):
            row_data = self.model.row_data(i)
            relationship_name = row_data[name_column]
            if not relationship_name:
                continue
            object_id_list = list()
            for column in range(name_column):  # Leave 'name' column outside
                object_name = row_data[column]
                if not object_name:
                    continue
                object_ = self._parent.db_map.single_object(name=object_name).one_or_none()
                if not object_:
                    continue
                object_id_list.append(object_.id)
            if len(object_id_list) < 2:
                continue
            wide_kwargs = {
                'name': relationship_name,
                'object_id_list': object_id_list,
                'class_id': self.relationship_class.id
            }
            wide_kwargs_list.append(wide_kwargs)
        try:
            wide_relationships = self._parent.db_map.add_wide_relationships(*wide_kwargs_list)
            self._parent.add_relationships(wide_relationships)
            super().accept()
        except SpineIntegrityError as e:
            self._parent.msg_error.emit(e.msg)
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class EditItemsDialog(QDialog):
    """A dialog to query user's preferences for updating items.

    Attributes:
        parent (TreeViewForm): data store widget
        orig_kwargs_list (list): orignal key word arguments
    """
    def __init__(self, parent, orig_kwargs_list):
        super().__init__(parent)
        self._parent = parent
        self.orig_kwargs_list = orig_kwargs_list
        self.ui = None
        self.model = MinimalTableModel(self)
        self.object_icon = QIcon(QPixmap(":/icons/object_icon.png"))
        self.font_metric = QFontMetrics(QFont("", 0))
        self.setAttribute(Qt.WA_DeleteOnClose)

    def setup_ui(self):
        self.ui = ui.edit_data_items.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def resize_tableview(self):
        table_width = self.font_metric.width('9999') + qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        for j in range(self.ui.tableView.horizontalHeader().count() - 1):
            table_width += self.ui.tableView.horizontalHeader().sectionSize(j)
        section = self.ui.tableView.horizontalHeader().count() - 1
        table_width += min(200, self.ui.tableView.horizontalHeader().sectionSize(section))
        self.ui.tableView.setMinimumWidth(table_width)


class EditObjectClassesDialog(EditItemsDialog):
    """A dialog to query user's preferences for updating object classes.

    Attributes:
        parent (TreeViewForm): data store widget
        orig_kwargs_list (list): list of dictionaries corresponding to object classes to edit/update
    """
    def __init__(self, parent, orig_kwargs_list):
        super().__init__(parent, orig_kwargs_list)
        self.setup_ui()
        self.setWindowTitle("Edit object classes")
        self.model.set_horizontal_header_labels(['object class name', 'description'])
        self.orig_data = list()
        self.id_list = list()
        for kwargs in orig_kwargs_list:
            try:
                self.id_list.append(kwargs["id"])
            except KeyError:
                continue
            try:
                name = kwargs["name"]
            except KeyError:
                continue
            try:
                description = kwargs["description"]
            except KeyError:
                description = None
            row_data = [name, description]
            self.orig_data.append(row_data)
        self.model.reset_model(self.orig_data)
        for row in range(self.model.rowCount()):
            index = self.model.index(row, 0)
            self.model.setData(index, self.object_icon, Qt.DecorationRole)
        self.resize_tableview()

    def resize_tableview(self):
        header = self.ui.tableView.horizontalHeader()
        header.resizeSection(0, 150)
        header.resizeSection(1, 200)
        super().resize_tableview()

    def accept(self):
        """Collect info from dialog and try to update items."""
        kwargs_list = list()
        for i in range(self.model.rowCount()):
            id = self.id_list[i]
            name, description = self.model.row_data(i)
            if not name:
                continue
            orig_name, orig_description = self.orig_data[i]
            if name == orig_name and description == orig_description:
                continue
            kwargs = {
                'id': id,
                'name': name,
                'description': description
            }
            kwargs_list.append(kwargs)
        try:
            object_classes = self._parent.db_map.update_object_classes(*kwargs_list)
            self._parent.update_object_classes(object_classes, self.orig_kwargs_list)
            super().accept()
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class EditObjectsDialog(EditItemsDialog):
    """A dialog to query user's preferences for updating objects.

    Attributes:
        parent (TreeViewForm): data store widget
        orig_kwargs_list (list): list of dictionaries corresponding to objects to edit/update
    """
    def __init__(self, parent, orig_kwargs_list):
        super().__init__(parent, orig_kwargs_list)
        self.setup_ui()
        self.setWindowTitle("Edit objects")
        self.model.set_horizontal_header_labels(['object name', 'description'])
        self.orig_data = list()
        self.id_list = list()
        for kwargs in orig_kwargs_list:
            try:
                self.id_list.append(kwargs["id"])
            except KeyError:
                continue
            try:
                name = kwargs["name"]
            except KeyError:
                continue
            try:
                description = kwargs["description"]
            except KeyError:
                description = None
            row_data = [name, description]
            self.orig_data.append(row_data)
        self.model.reset_model(self.orig_data)
        self.resize_tableview()

    def resize_tableview(self):
        header = self.ui.tableView.horizontalHeader()
        header.resizeSection(0, 150)
        header.resizeSection(1, 200)
        super().resize_tableview()

    def accept(self):
        """Collect info from dialog and try to update items."""
        kwargs_list = list()
        for i in range(self.model.rowCount()):
            id = self.id_list[i]
            name, description = self.model.row_data(i)
            if not name:
                continue
            orig_name, orig_description = self.orig_data[i]
            if name == orig_name and description == orig_description:
                continue
            kwargs = {
                'id': id,
                'name': name,
                'description': description
            }
            kwargs_list.append(kwargs)
        try:
            objects = self._parent.db_map.update_objects(*kwargs_list)
            self._parent.update_objects(objects, self.orig_kwargs_list)
            super().accept()
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class EditRelationshipClassesDialog(EditItemsDialog):
    """A dialog to query user's preferences for updating relationship classes.

    Attributes:
        parent (TreeViewForm): data store widget
        orig_kwargs_list (list): list of dictionaries corresponding to relationship classes to edit/update
    """
    def __init__(self, parent, orig_kwargs_list):
        super().__init__(parent, orig_kwargs_list)
        self.setup_ui()
        self.setWindowTitle("Edit relationship classes")
        self.model.set_horizontal_header_labels(['relationship class name'])
        self.orig_data = list()
        self.id_list = list()
        for kwargs in orig_kwargs_list:
            try:
                self.id_list.append(kwargs["id"])
            except KeyError:
                continue
            try:
                name = kwargs["name"]
            except KeyError:
                continue
            row_data = [name]
            self.orig_data.append(row_data)
        self.model.reset_model(self.orig_data)
        self.resize_tableview()

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        header.resizeSection(0, 200)
        super().resize_tableview()

    def accept(self):
        """Collect info from dialog and try to update items."""
        kwargs_list = list()
        for i in range(self.model.rowCount()):
            id = self.id_list[i]
            name = self.model.row_data(i)[0]
            if not name:
                continue
            orig_name = self.orig_data[i][0]
            if name == orig_name:
                continue
            kwargs = {
                'id': id,
                'name': name
            }
            kwargs_list.append(kwargs)
        try:
            wide_relationship_classes = self._parent.db_map.update_wide_relationship_classes(*kwargs_list)
            self._parent.update_relationship_classes(wide_relationship_classes, self.orig_kwargs_list)
            super().accept()
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class EditRelationshipsDialog(EditItemsDialog):
    """A dialog to query user's preferences for updating relationships.

    Attributes:
        parent (TreeViewForm): data store widget
        orig_kwargs_list (list): list of dictionaries corresponding to relationships to edit/update
        relationship_class (KeyedTuple): the relationship class item (all edited relationships must be of this class)
    """
    def __init__(self, parent, orig_kwargs_list, relationship_class):
        super().__init__(parent, orig_kwargs_list)
        self.setup_ui()
        self.setWindowTitle("Edit relationships")
        object_class_name_list = relationship_class.object_class_name_list.split(",")
        self.model.set_horizontal_header_labels([*[x + ' name' for x in object_class_name_list], 'relationship name'])
        self.orig_data = list()
        self.orig_object_id_lists = list()
        self.id_list = list()
        for kwargs in orig_kwargs_list:
            try:
                self.id_list.append(kwargs["id"])
            except KeyError:
                continue
            try:
                object_name_list = kwargs["object_name_list"].split(',')
                object_id_list = [int(x) for x in kwargs["object_id_list"].split(',')]
                name = kwargs["name"]
            except KeyError:
                continue
            row_data = [*object_name_list, name]
            self.orig_data.append(row_data)
            self.orig_object_id_lists.append(object_id_list)
        self.model.reset_model(self.orig_data)
        for row in range(self.model.rowCount()):
            for column in range(self.model.columnCount() - 1):
                index = self.model.index(row, column)
                self.model.setData(index, self.object_icon, Qt.DecorationRole)
        self.ui.tableView.setItemDelegate(AddRelationshipsDelegate(self.ui.tableView, parent.db_map))
        self.ui.tableView.itemDelegate().commit_model_data.connect(self.data_committed)
        self.resize_tableview()

    @Slot("QModelIndex", "QVariant", name='data_committed')
    def data_committed(self, index, data):
        """Update 'object x' field with data from combobox editor."""
        if data is None:
            return
        self.model.setData(index, data, Qt.EditRole)

    def resize_tableview(self):
        self.ui.tableView.resizeColumnsToContents()
        header = self.ui.tableView.horizontalHeader()
        super().resize_tableview()

    def accept(self):
        """Collect info from dialog and try to update items."""
        kwargs_list = list()
        name_column = self.model.columnCount() - 1
        for i in range(self.model.rowCount()):
            id = self.id_list[i]
            orig_object_id_list = self.orig_object_id_lists[i]
            row_data = self.model.row_data(i)
            orig_row_data = self.orig_data[i]
            relationship_name = row_data[name_column]
            orig_relationship_name = orig_row_data[name_column]
            if not relationship_name:
                continue
            object_id_list = list()
            for column in range(name_column):  # Leave 'name' column outside
                object_name = row_data[column]
                if not object_name:
                    continue
                object_ = self._parent.db_map.single_object(name=object_name).one_or_none()
                if not object_:
                    continue
                object_id_list.append(object_.id)
            if len(object_id_list) < 2:
                continue
            if orig_relationship_name == relationship_name and orig_object_id_list == object_id_list:
                continue
            kwargs = {
                'id': id,
                'name': relationship_name,
                'object_id_list': object_id_list
            }
            kwargs_list.append(kwargs)
        try:
            wide_relationships = self._parent.db_map.update_wide_relationships(*kwargs_list)
            self._parent.update_relationships(wide_relationships, self.orig_kwargs_list)
            super().accept()
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class CommitDialog(QDialog):
    """A dialog to query user's preferences for new parameter values.

    Attributes:
        parent (TreeViewForm): data store widget
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
        self.actionAccept = QAction(self)
        self.actionAccept.setShortcut(QApplication.translate("Dialog", "Ctrl+Return", None, -1))
        self.actionAccept.triggered.connect(self.accept)
        self.actionAccept.setEnabled(False)
        self.commit_msg_edit = QPlainTextEdit(self)
        self.commit_msg_edit.setPlaceholderText('Commit message \t(press Ctrl+Enter to commit)')
        self.commit_msg_edit.addAction(self.actionAccept)
        button_box = QDialogButtonBox()
        button_box.addButton(QDialogButtonBox.Cancel)
        self.commit_button = button_box.addButton('Commit', QDialogButtonBox.AcceptRole)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        inner_layout.addWidget(self.commit_msg_edit)
        inner_layout.addWidget(button_box)
        # Add status bar to form
        form.addLayout(inner_layout)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.commit_msg_edit.textChanged.connect(self.receive_text_changed)
        self.receive_text_changed()

    @Slot(name="receive_text_changed")
    def receive_text_changed(self):
        """Called when text changes in the commit msg text edit.
        Enable/disable commit button accordingly."""
        self.commit_msg = self.commit_msg_edit.toPlainText()
        cond = self.commit_msg.strip() != ""
        self.commit_button.setEnabled(cond)
        self.actionAccept.setEnabled(cond)
