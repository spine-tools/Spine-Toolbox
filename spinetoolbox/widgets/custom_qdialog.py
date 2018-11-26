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
    QDialogButtonBox, QComboBox, QHeaderView, QStatusBar, QStyle, QAction, QApplication, QToolButton
from PySide2.QtCore import Signal, Slot, Qt, QSize
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
from helpers import busy_effect, object_pixmap


class AddItemsDialog(QDialog):
    """A dialog to query user's preferences for new object classes.

    Attributes:
        parent (TreeViewForm): data store widget
        force_default (bool): if True, defaults are non-editable
    """
    def __init__(self, parent, force_default=False):
        super().__init__(parent)
        self._parent = parent
        self.ui = None
        self.model = MinimalTableModel(self, can_grow=True, has_empty_row=True)
        self.model._force_default = force_default
        self.remove_row_icon = None  # Set in subclasses to a custom one
        self.setAttribute(Qt.WA_DeleteOnClose)

    def setup_ui(self, ui_dialog):
        self.ui = ui_dialog
        self.ui.setupUi(self)
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.tableView.itemDelegate().commit_model_data.connect(self.data_committed)
        self.model.dataChanged.connect(self.model_data_changed)
        self.model.modelReset.connect(self.model_reset)
        self.model.rowsInserted.connect(self.model_rows_inserted)

    @Slot(name="model_reset")
    def model_reset(self):
        self.model.insertColumns(self.model.columnCount(), 1)
        self.model.insert_horizontal_header_labels(self.model.columnCount(), [""])
        self.ui.tableView.horizontalHeader().resizeSection(self.model.columnCount() - 1, 32)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(self.model.columnCount() - 1, QHeaderView.Fixed)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(self.model.columnCount() - 2, QHeaderView.Stretch)

    @Slot("QModelIndex", "int", "int", name="model_rows_inserted")
    def model_rows_inserted(self, parent, first, last):
        column = self.model.columnCount() - 1
        for row in range(first, last + 1):
            index = self.model.index(row, column, parent)
            action = QAction()
            action.setIcon(self.remove_row_icon)
            button = QToolButton()
            button.setDefaultAction(action)
            button.setIconSize(QSize(20, 20))
            self.ui.tableView.setIndexWidget(index, button)
            action.triggered.connect(lambda: self.remove_clicked_row(button))

    def remove_clicked_row(self, button):
        column = self.model.columnCount() - 1
        for row in range(self.model.rowCount()):
            index = self.model.index(row, column)
            if button == self.ui.tableView.indexWidget(index):
                self.model.removeRows(row, 1)
                break

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
        self.remove_row_icon = QIcon(QPixmap(":/icons/minus_object_icon.png"))
        self.setup_ui(ui.add_object_classes.Ui_Dialog())
        self.ui.tableView.setItemDelegate(LineEditDelegate(parent))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['object class name', 'description'])
        self.model.clear()
        # Add items to combobox
        insert_position_list = ['Insert new classes at the top']
        insert_position_list.extend(
            ["Insert new classes after '{}'".format(i.name) for i in self.object_class_list])
        self.ui.comboBox.addItems(insert_position_list)
        self.ui.tableView.resizeColumnsToContents()

    @busy_effect
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
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)[:-1]
            name, description = row_data
            if not name:
                self._parent.msg_error.emit("Object class name missing at row {0}".format(i + 1))
                return
            kwargs = {
                'name': name,
                'description': description,
                'display_order': display_order
            }
            kwargs_list.append(kwargs)
        if not kwargs_list:
            self._parent.msg_error.emit("Nothing to add")
            return
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
        force_default (bool): if True, defaults are non-editable
    """
    def __init__(self, parent, class_id=None, force_default=False):
        super().__init__(parent, force_default=force_default)
        self.remove_row_icon = QIcon(QPixmap(":/icons/minus_object_icon.png"))
        self.setup_ui(ui.add_objects.Ui_Dialog())
        self.ui.tableView.setItemDelegate(AddObjectsDelegate(parent))
        self.connect_signals()
        default_class = self._parent.db_map.single_object_class(id=class_id).one_or_none()
        self.default_class_name = default_class.name if default_class else None
        self.model.set_horizontal_header_labels(['object class name', 'object name', 'description'])
        self.model.set_default_row([self.default_class_name])
        self.model.clear()
        self.ui.tableView.resizeColumnsToContents()

    @Slot("QModelIndex", "QModelIndex", "QVector", name="model_data_changed")
    def model_data_changed(self, top_left, bottom_right, roles):
        """Set decoration role data."""
        if Qt.EditRole not in roles:
            return
        header = self.model.horizontal_header_labels()
        top = top_left.row()
        left = top_left.column()
        bottom = bottom_right.row()
        right = bottom_right.column()
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                if header[column] != 'object class name':
                    continue
                index = self.model.index(row, column)
                object_class_name = index.data(Qt.DisplayRole)
                if not object_class_name:
                    return
                icon = QIcon(object_pixmap(object_class_name))
                self.model.setData(index, icon, Qt.DecorationRole)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to add items."""
        kwargs_list = list()
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)[:-1]
            class_name, name, description = row_data
            if not class_name:
                self._parent.msg_error.emit("Object class name missing at row {}".format(i + 1))
                return
            if not name:
                self._parent.msg_error.emit("Object name missing at row {}".format(i + 1))
                return
            class_ = self._parent.db_map.single_object_class(name=class_name).one_or_none()
            if not class_:
                self._parent.msg_error.emit("Couldn't find object class '{}' at row {}".format(class_name, i + 1))
                return
            kwargs = {
                'class_id': class_.id,
                'name': name,
                'description': description
            }
            kwargs_list.append(kwargs)
        if not kwargs_list:
            self._parent.msg_error.emit("Nothing to add")
            return
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
    def __init__(self, parent, object_class_one_id=None, force_default=False):
        super().__init__(parent, force_default=force_default)
        self.remove_row_icon = QIcon(QPixmap(":/icons/minus_relationship_icon.png"))
        self.setup_ui(ui.add_relationship_classes.Ui_Dialog())
        self.ui.tableView.setItemDelegate(AddRelationshipClassesDelegate(parent))
        self.connect_signals()
        self.number_of_dimensions = 2
        self.object_class_one_name = None
        if object_class_one_id:
            object_class_one = self._parent.db_map.single_object_class(id=object_class_one_id).one_or_none()
            if object_class_one:
                self.object_class_one_name = object_class_one.name
        self.model.set_horizontal_header_labels(
            ['object class 1 name', 'object class 2 name', 'relationship class name'])
        self.model.set_default_row([self.object_class_one_name])
        self.model.clear()
        self.ui.tableView.resizeColumnsToContents()

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.spinBox.valueChanged.connect(self.insert_or_remove_column)
        super().connect_signals()

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
        self.model.insertColumns(column, 1)
        self.ui.tableView.resizeColumnToContents(column)

    def remove_column(self):
        self.number_of_dimensions -= 1
        column = self.number_of_dimensions
        column_size = self.ui.tableView.horizontalHeader().sectionSize(column)
        self.model.header.pop(column)
        try:
            self.model.default_row.pop(column)
        except IndexError:
            pass
        self.model.removeColumns(column, 1)
        # Add removed column size to description column size
        column_size += self.ui.tableView.horizontalHeader().sectionSize(column)
        self.ui.tableView.horizontalHeader().resizeSection(column, column_size)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="model_data_changed")
    def model_data_changed(self, top_left, bottom_right, roles):
        if Qt.EditRole not in roles:
            return
        header = self.model.horizontal_header_labels()
        top = top_left.row()
        left = top_left.column()
        bottom = bottom_right.row()
        right = bottom_right.column()
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                if header[column] == 'relationship class name':
                    continue
                index = self.model.index(row, column)
                object_class_name = index.data(Qt.DisplayRole)
                if not object_class_name:
                    continue
                icon = QIcon(object_pixmap(object_class_name))
                self.model.setData(index, icon, Qt.DecorationRole)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to add items."""
        wide_kwargs_list = list()
        name_column = self.model.horizontal_header_labels().index("relationship class name")
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)[:-1]
            relationship_class_name = row_data[name_column]
            if not relationship_class_name:
                self._parent.msg_error.emit("Relationship class name missing at row {}".format(i + 1))
                return
            object_class_id_list = list()
            for column in range(name_column):  # Leave 'name' column outside
                object_class_name = row_data[column]
                if not object_class_name:
                    self._parent.msg_error.emit("Object class name missing at row {}".format(i + 1))
                    return
                object_class = self._parent.db_map.single_object_class(name=object_class_name).one_or_none()
                if not object_class:
                    self._parent.msg_error.emit(
                        "Couldn't find object class '{}' at row {}".format(object_class_name, i + 1))
                    return
                object_class_id_list.append(object_class.id)
            if len(object_class_id_list) < 2:
                self._parent.msg_error.emit("Not enough dimensions at row {} (at least two are needed)".format(i + 1))
                return
            wide_kwargs = {
                'name': relationship_class_name,
                'object_class_id_list': object_class_id_list
            }
            wide_kwargs_list.append(wide_kwargs)
        if not wide_kwargs_list:
            self._parent.msg_error.emit("Nothing to add")
            return
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
    def __init__(self, parent, relationship_class_id=None, object_id=None, object_class_id=None, force_default=False):
        super().__init__(parent, force_default=force_default)
        self.remove_row_icon = QIcon(QPixmap(":/icons/minus_relationship_icon.png"))
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
        self.ui.tableView.setItemDelegate(AddRelationshipsDelegate(parent))
        self.init_relationship_class(force_default)
        # Add status bar to form
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        self.connect_signals()
        self.reset_model()

    def init_relationship_class(self, force_default):
        """Populate combobox and initialize relationship class if any."""
        relationship_class_name_list = [x.name for x in self.relationship_class_list]
        if not force_default:
            self.ui.comboBox_relationship_class.addItems(relationship_class_name_list)
            self.ui.comboBox_relationship_class.setCurrentIndex(-1)
        self.relationship_class = self._parent.db_map.\
            single_wide_relationship_class(id=self.relationship_class_id).one_or_none()
        if not self.relationship_class:
            # Default not found
            return
        try:
            if not force_default:
                combo_index = relationship_class_name_list.index(self.relationship_class.name)
                self.ui.comboBox_relationship_class.setCurrentIndex(combo_index)
                return
            self.ui.comboBox_relationship_class.addItem(self.relationship_class.name)
        except ValueError:
            pass

    def connect_signals(self):
        """Connect signals to slots."""
        self.ui.comboBox_relationship_class.currentIndexChanged.connect(self.call_reset_model)
        super().connect_signals()

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
            self.model.set_default_row(defaults)
        self.model.clear()
        self.ui.tableView.resizeColumnsToContents()

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

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to add items."""
        wide_kwargs_list = list()
        name_column = self.model.horizontal_header_labels().index("relationship name")
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)[:-1]
            relationship_name = row_data[name_column]
            if not relationship_name:
                self._parent.msg_error.emit("Relationship name missing at row {}".format(i + 1))
                return
            object_id_list = list()
            for column in range(name_column):  # Leave 'name' column outside
                object_name = row_data[column]
                if not object_name:
                    self._parent.msg_error.emit("Object name missing at row {}".format(i + 1))
                    return
                object_ = self._parent.db_map.single_object(name=object_name).one_or_none()
                if not object_:
                    self._parent.msg_error.emit("Couldn't find object '{}' at row {}".format(object_name, i + 1))
                    return
                object_id_list.append(object_.id)
            if len(object_id_list) < 2:
                self._parent.msg_error.emit("Not enough dimensions at row {} (at least two are needed)".format(i + 1))
                return
            wide_kwargs = {
                'name': relationship_name,
                'object_id_list': object_id_list,
                'class_id': self.relationship_class.id
            }
            wide_kwargs_list.append(wide_kwargs)
        if not wide_kwargs_list:
            self._parent.msg_error.emit("Nothing to add")
            return
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
        kwargs_list (list): orignal key word arguments
    """
    def __init__(self, parent, kwargs_list):
        super().__init__(parent)
        self._parent = parent
        self.ui = None
        self.model = MinimalTableModel(self)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def setup_ui(self):
        self.ui = ui.edit_data_items.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)


class EditObjectClassesDialog(EditItemsDialog):
    """A dialog to query user's preferences for updating object classes.

    Attributes:
        parent (TreeViewForm): data store widget
        kwargs_list (list): list of dictionaries corresponding to object classes to edit/update
    """
    def __init__(self, parent, kwargs_list):
        super().__init__(parent, kwargs_list)
        self.setup_ui()
        self.setWindowTitle("Edit object classes")
        self.model.set_horizontal_header_labels(['object class name', 'description'])
        self.orig_data = list()
        self.id_list = list()
        model_data = list()
        for kwargs in kwargs_list:
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
            self.orig_data.append(row_data.copy())
            model_data.append(row_data)
        self.model.reset_model(model_data)
        self.ui.tableView.resizeColumnsToContents()

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to update items."""
        kwargs_list = list()
        for i in range(self.model.rowCount()):
            id = self.id_list[i]
            name, description = self.model.row_data(i)
            if not name:
                self._parent.msg_error.emit("Object class name missing at row {}".format(i + 1))
                return
            orig_name, orig_description = self.orig_data[i]
            if name == orig_name and description == orig_description:
                continue
            kwargs = {
                'id': id,
                'name': name,
                'description': description
            }
            kwargs_list.append(kwargs)
        if not kwargs_list:
            self._parent.msg_error.emit("Nothing to update")
            return
        try:
            object_classes = self._parent.db_map.update_object_classes(*kwargs_list)
            self._parent.update_object_classes(object_classes)
            super().accept()
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class EditObjectsDialog(EditItemsDialog):
    """A dialog to query user's preferences for updating objects.

    Attributes:
        parent (TreeViewForm): data store widget
        kwargs_list (list): list of dictionaries corresponding to objects to edit/update
    """
    def __init__(self, parent, kwargs_list):
        super().__init__(parent, kwargs_list)
        self.setup_ui()
        self.setWindowTitle("Edit objects")
        self.model.set_horizontal_header_labels(['object name', 'description'])
        self.orig_data = list()
        self.id_list = list()
        model_data = list()
        for kwargs in kwargs_list:
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
            self.orig_data.append(row_data.copy())
            model_data.append(row_data)
        self.model.reset_model(model_data)
        self.ui.tableView.resizeColumnsToContents()

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to update items."""
        kwargs_list = list()
        for i in range(self.model.rowCount()):
            id = self.id_list[i]
            name, description = self.model.row_data(i)
            if not name:
                self._parent.msg_error.emit("Object name missing at row {}".format(i + 1))
                return
            orig_name, orig_description = self.orig_data[i]
            if name == orig_name and description == orig_description:
                continue
            kwargs = {
                'id': id,
                'name': name,
                'description': description
            }
            kwargs_list.append(kwargs)
        if not kwargs_list:
            self._parent.msg_error.emit("Nothing to update")
            return
        try:
            objects = self._parent.db_map.update_objects(*kwargs_list)
            self._parent.update_objects(objects)
            super().accept()
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class EditRelationshipClassesDialog(EditItemsDialog):
    """A dialog to query user's preferences for updating relationship classes.

    Attributes:
        parent (TreeViewForm): data store widget
        kwargs_list (list): list of dictionaries corresponding to relationship classes to edit/update
    """
    def __init__(self, parent, kwargs_list):
        super().__init__(parent, kwargs_list)
        self.setup_ui()
        self.setWindowTitle("Edit relationship classes")
        self.model.set_horizontal_header_labels(['relationship class name'])
        self.orig_data = list()
        self.id_list = list()
        model_data = list()
        for kwargs in kwargs_list:
            try:
                self.id_list.append(kwargs["id"])
            except KeyError:
                continue
            try:
                name = kwargs["name"]
            except KeyError:
                continue
            row_data = [name]
            self.orig_data.append(row_data.copy())
            model_data.append(row_data)
        self.model.reset_model(model_data)
        self.ui.tableView.resizeColumnsToContents()

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to update items."""
        kwargs_list = list()
        for i in range(self.model.rowCount()):
            id = self.id_list[i]
            name = self.model.row_data(i)[0]
            if not name:
                self._parent.msg_error.emit("Relationship class name missing at row {}".format(i + 1))
                return
            orig_name = self.orig_data[i][0]
            if name == orig_name:
                continue
            kwargs = {
                'id': id,
                'name': name
            }
            kwargs_list.append(kwargs)
        if not kwargs_list:
            self._parent.msg_error.emit("Nothing to update")
            return
        try:
            wide_relationship_classes = self._parent.db_map.update_wide_relationship_classes(*kwargs_list)
            self._parent.update_relationship_classes(wide_relationship_classes)
            super().accept()
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class EditRelationshipsDialog(EditItemsDialog):
    """A dialog to query user's preferences for updating relationships.

    Attributes:
        parent (TreeViewForm): data store widget
        kwargs_list (list): list of dictionaries corresponding to relationships to edit/update
        relationship_class (KeyedTuple): the relationship class item (all edited relationships must be of this class)
    """
    def __init__(self, parent, kwargs_list, relationship_class):
        super().__init__(parent, kwargs_list)
        self.setup_ui()
        self.setWindowTitle("Edit relationships")
        object_class_name_list = relationship_class.object_class_name_list.split(",")
        self.model.set_horizontal_header_labels([*[x + ' name' for x in object_class_name_list], 'relationship name'])
        self.orig_data = list()
        self.orig_object_id_lists = list()
        self.id_list = list()
        model_data = list()
        for kwargs in kwargs_list:
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
            self.orig_object_id_lists.append(object_id_list)
            self.orig_data.append(row_data.copy())
            model_data.append(row_data)
        self.model.reset_model(model_data)
        self.ui.tableView.setItemDelegate(AddRelationshipsDelegate(parent))
        self.ui.tableView.itemDelegate().commit_model_data.connect(self.data_committed)
        self.ui.tableView.resizeColumnsToContents()

    @Slot("QModelIndex", "QVariant", name='data_committed')
    def data_committed(self, index, data):
        """Update 'object x' field with data from combobox editor."""
        if data is None:
            return
        self.model.setData(index, data, Qt.EditRole)

    @busy_effect
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
                self._parent.msg_error.emit("Relationship name missing at row {}".format(i + 1))
                return
            object_id_list = list()
            for column in range(name_column):  # Leave 'name' column outside
                object_name = row_data[column]
                if not object_name:
                    self._parent.msg_error.emit("Object name missing at row {}".format(i + 1))
                    return
                object_ = self._parent.db_map.single_object(name=object_name).one_or_none()
                if not object_:
                    self._parent.msg_error.emit("Couldn't find object '{}' at row {}".format(object_name, i + 1))
                    return
                object_id_list.append(object_.id)
            if len(object_id_list) < 2:
                self._parent.msg_error.emit("Not enough dimensions at row {} (at least two are needed)".format(i + 1))
                return
            if orig_relationship_name == relationship_name and orig_object_id_list == object_id_list:
                continue
            kwargs = {
                'id': id,
                'name': relationship_name,
                'object_id_list': object_id_list
            }
            kwargs_list.append(kwargs)
        if not kwargs_list:
            self._parent.msg_error.emit("Nothing to update")
            return
        try:
            wide_relationships = self._parent.db_map.update_wide_relationships(*kwargs_list)
            self._parent.update_relationships(wide_relationships)
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
