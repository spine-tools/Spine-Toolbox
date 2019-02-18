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

:author: M. Marin (KTH)
:date:   13.5.2018
"""

import logging
from copy import deepcopy
from PySide2.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPlainTextEdit, QLineEdit, \
    QDialogButtonBox, QHeaderView, QAction, QApplication, QToolButton, QWidget, QLabel, \
    QComboBox, QSpinBox
from PySide2.QtCore import Signal, Slot, Qt, QSize
from PySide2.QtGui import QFont, QFontMetrics, QIcon, QPixmap
from spinedatabase_api import SpineDBAPIError, SpineIntegrityError
from models import EmptyRowModel, MinimalTableModel, HybridTableModel
from widgets.custom_delegates import AddObjectsDelegate, AddRelationshipClassesDelegate, AddRelationshipsDelegate, \
    AddParameterEnumsDelegate, LineEditDelegate
from widgets.custom_qtableview import CopyPasteTableView
from helpers import busy_effect, object_pixmap


class ManageItemsDialog(QDialog):
    """A dialog with a CopyPasteTableView and a QDialogButtonBox, to be extended into
    dialogs to query user's preferences for adding/editing/managing data items

    Attributes:
        parent (TreeViewForm): data store widget
        force_default (bool): if True, defaults are non-editable
    """
    def __init__(self, parent, force_default=False):
        super().__init__(parent)
        self._parent = parent
        self.table_view = CopyPasteTableView(self)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.button_box = QDialogButtonBox(self)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        layout = QVBoxLayout(self)
        layout.addWidget(self.table_view)
        layout.addWidget(self.button_box)
        self.remove_row_icon = None  # Set in subclasses to a custom one
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.table_view.itemDelegate().data_committed.connect(self._handle_data_committed)
        self.model.dataChanged.connect(self._handle_model_data_changed)
        self.model.modelReset.connect(self._handle_model_reset)
        self.model.rowsInserted.connect(self._handle_model_rows_inserted)

    @Slot(name="_handle_model_reset")
    def _handle_model_reset(self):
        self.model.insert_horizontal_header_labels(self.model.columnCount(), [""])
        self.table_view.horizontalHeader().resizeSection(self.model.columnCount() - 1, 32)
        self.table_view.horizontalHeader().setSectionResizeMode(self.model.columnCount() - 1, QHeaderView.Fixed)
        self.table_view.horizontalHeader().setSectionResizeMode(self.model.columnCount() - 2, QHeaderView.Stretch)

    @Slot("QModelIndex", "int", "int", name="_handle_model_rows_inserted")
    def _handle_model_rows_inserted(self, parent, first, last):
        column = self.model.columnCount() - 1
        for row in range(first, last + 1):
            index = self.model.index(row, column, parent)
            self.create_remove_row_button(index)

    def create_remove_row_button(self, index):
        """Create button to remove row."""
        action = QAction()
        action.setIcon(self.remove_row_icon)
        button = QToolButton()
        button.setDefaultAction(action)
        button.setIconSize(QSize(20, 20))
        self.table_view.setIndexWidget(index, button)
        action.triggered.connect(lambda: self.remove_clicked_row(button))

    def remove_clicked_row(self, button):
        column = self.model.columnCount() - 1
        for row in range(self.model.rowCount()):
            index = self.model.index(row, column)
            if button == self.table_view.indexWidget(index):
                self.model.removeRows(row, 1)
                break

    @Slot("QModelIndex", "QVariant", name='_handle_data_committed')
    def _handle_data_committed(self, index, data):
        """Update model data."""
        if data is None:
            return
        self.model.setData(index, data, Qt.EditRole)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="_handle_model_data_changed")
    def _handle_model_data_changed(self, top_left, bottom_right, roles):
        """Reimplement this method in subclasses to handle changes in model data."""
        pass


class AddObjectClassesDialog(ManageItemsDialog):
    """A dialog to query user's preferences for new object classes.

    Attributes:
        parent (TreeViewForm): data store widget
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Add object classes")
        self.model = EmptyRowModel(self)
        self.table_view.setModel(self.model)
        self.combo_box = QComboBox(self)
        self.layout().insertWidget(0, self.combo_box)
        self.object_class_list = self._parent.db_map.object_class_list()
        self.remove_row_icon = QIcon(":/icons/minus_object_icon.png")
        self.table_view.setItemDelegate(LineEditDelegate(parent))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['object class name', 'description'])
        self.model.clear()
        self.table_view.resizeColumnsToContents()
        insert_at_position_list = ['Insert new classes at the top']
        insert_at_position_list.extend(
            ["Insert new classes after '{}'".format(i.name) for i in self.object_class_list])
        self.combo_box.addItems(insert_at_position_list)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to add items."""
        kwargs_list = list()
        index = self.combo_box.currentIndex()
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


class AddObjectsDialog(ManageItemsDialog):
    """A dialog to query user's preferences for new objects.

    Attributes:
        parent (TreeViewForm): data store widget
        class_id (int): default object class id
        force_default (bool): if True, defaults are non-editable
    """
    def __init__(self, parent, class_id=None, force_default=False):
        super().__init__(parent)
        self.setWindowTitle("Add objects")
        self.model = EmptyRowModel(self)
        self.model.force_default = force_default
        self.table_view.setModel(self.model)
        self.remove_row_icon = QIcon(":/icons/minus_object_icon.png")
        self.table_view.setItemDelegate(AddObjectsDelegate(parent))
        self.connect_signals()
        default_class = self._parent.db_map.single_object_class(id=class_id).one_or_none()
        self.default_class_name = default_class.name if default_class else None
        self.model.set_horizontal_header_labels(['object class name', 'object name', 'description'])
        self.model.set_default_row(**{'object class name': self.default_class_name})
        self.model.clear()
        self.table_view.resizeColumnsToContents()

    @Slot("QModelIndex", "QModelIndex", "QVector", name="_handle_model_data_changed")
    def _handle_model_data_changed(self, top_left, bottom_right, roles):
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


class AddRelationshipClassesDialog(ManageItemsDialog):
    """A dialog to query user's preferences for new relationship classes.

    Attributes:
        parent (TreeViewForm): data store widget
        object_class_one_id (int): default object class id to put in dimension '1'
    """
    def __init__(self, parent, object_class_one_id=None, force_default=False):
        super().__init__(parent)
        self.setWindowTitle("Add relationship classes")
        self.model = EmptyRowModel(self)
        self.model.force_default = force_default
        self.table_view.setModel(self.model)
        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.addWidget(QLabel("Number of dimensions"))
        self.spin_box = QSpinBox(self)
        self.spin_box.setMinimum(2)
        layout.addWidget(self.spin_box)
        layout.addStretch()
        self.layout().insertWidget(0, widget)
        self.remove_row_icon = QIcon(":/icons/minus_relationship_icon.png")
        self.table_view.setItemDelegate(AddRelationshipClassesDelegate(parent))
        self.number_of_dimensions = 2
        self.object_class_one_name = None
        if object_class_one_id:
            object_class_one = self._parent.db_map.single_object_class(id=object_class_one_id).one_or_none()
            if object_class_one:
                self.object_class_one_name = object_class_one.name
        self.connect_signals()
        self.model.set_horizontal_header_labels(
            ['object class 1 name', 'object class 2 name', 'relationship class name'])
        self.model.set_default_row(**{'object class 1 name': self.object_class_one_name})
        self.model.clear()
        self.table_view.resizeColumnsToContents()

    def connect_signals(self):
        """Connect signals to slots."""
        self.spin_box.valueChanged.connect(self._handle_spin_box_value_changed)
        super().connect_signals()

    @Slot("int", name="_handle_spin_box_value_changed")
    def _handle_spin_box_value_changed(self, i):
        self.spin_box.setEnabled(False)
        if i > self.number_of_dimensions:
            self.insert_column()
        elif i < self.number_of_dimensions:
            self.remove_column()
        self.spin_box.setEnabled(True)

    def insert_column(self):
        column = self.number_of_dimensions
        self.number_of_dimensions += 1
        column_name = "object class {} name".format(self.number_of_dimensions)
        self.model.insertColumns(column, 1)
        self.model.insert_horizontal_header_labels(column, [column_name])
        self.table_view.resizeColumnToContents(column)

    def remove_column(self):
        self.number_of_dimensions -= 1
        column = self.number_of_dimensions
        column_size = self.table_view.horizontalHeader().sectionSize(column)
        self.model.header.pop(column)
        self.model.removeColumns(column, 1)
        # Add removed column size to relationship class name column size
        column_size += self.table_view.horizontalHeader().sectionSize(column)
        self.table_view.horizontalHeader().resizeSection(column, column_size)

    @Slot("QModelIndex", "QModelIndex", "QVector", name="_handle_model_data_changed")
    def _handle_model_data_changed(self, top_left, bottom_right, roles):
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


class AddRelationshipsDialog(ManageItemsDialog):
    """A dialog to query user's preferences for new relationships.

    Attributes:
        parent (TreeViewForm): data store widget
        relationship_class_id (int): default relationship class id
        object_id (int): default object id
        object_class_id (int): default object class id
    """
    def __init__(self, parent, relationship_class_id=None, object_id=None, object_class_id=None, force_default=False):
        super().__init__(parent)
        self.setWindowTitle("Add relationships")
        self.model = EmptyRowModel(self)
        self.model.force_default = force_default
        self.table_view.setModel(self.model)
        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.addWidget(QLabel("Relationship class"))
        self.combo_box = QComboBox(self)
        layout.addWidget(self.combo_box)
        layout.addStretch()
        self.layout().insertWidget(0, widget)
        self.remove_row_icon = QIcon(":/icons/minus_relationship_icon.png")
        self.relationship_class_list = \
            [x for x in self._parent.db_map.wide_relationship_class_list(object_class_id=object_class_id)]
        self.relationship_class = None
        self.relationship_class_id = relationship_class_id
        self.object_id = object_id
        self.object_class_id = object_class_id
        self.default_object_column = None
        self.default_object_name = None
        self.set_default_object_name()
        self.table_view.setItemDelegate(AddRelationshipsDelegate(parent))
        self.init_relationship_class(force_default)
        self.connect_signals()
        self.reset_model()

    def init_relationship_class(self, force_default):
        """Populate combobox and initialize relationship class if any."""
        relationship_class_name_list = [x.name for x in self.relationship_class_list]
        if not force_default:
            self.combo_box.addItems(relationship_class_name_list)
            self.combo_box.setCurrentIndex(-1)
        self.relationship_class = self._parent.db_map.\
            single_wide_relationship_class(id=self.relationship_class_id).one_or_none()
        if not self.relationship_class:
            # Default not found
            return
        try:
            if not force_default:
                combo_index = relationship_class_name_list.index(self.relationship_class.name)
                self.combo_box.setCurrentIndex(combo_index)
                return
            self.combo_box.addItem(self.relationship_class.name)
        except ValueError:
            pass

    def connect_signals(self):
        """Connect signals to slots."""
        self.combo_box.currentIndexChanged.connect(self.call_reset_model)
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
            defaults = {header[self.default_object_column]: self.default_object_name}
            self.model.set_default_row(**defaults)
        self.model.clear()
        self.table_view.resizeColumnsToContents()

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


class EditObjectClassesDialog(ManageItemsDialog):
    """A dialog to query user's preferences for updating object classes.

    Attributes:
        parent (TreeViewForm): data store widget
        kwargs_list (list): list of dictionaries corresponding to object classes to edit/update
    """
    def __init__(self, parent, kwargs_list):
        super().__init__(parent, kwargs_list)
        self.setWindowTitle("Edit object classes")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(LineEditDelegate(parent))
        self.table_view.horizontalHeader().setStretchLastSection(True)
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
        self.table_view.resizeColumnsToContents()
        self.connect_signals()

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


class EditObjectsDialog(ManageItemsDialog):
    """A dialog to query user's preferences for updating objects.

    Attributes:
        parent (TreeViewForm): data store widget
        kwargs_list (list): list of dictionaries corresponding to objects to edit/update
    """
    def __init__(self, parent, kwargs_list):
        super().__init__(parent, kwargs_list)
        self.setWindowTitle("Edit objects")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(LineEditDelegate(parent))
        self.table_view.horizontalHeader().setStretchLastSection(True)
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
        self.table_view.resizeColumnsToContents()
        self.connect_signals()

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


class EditRelationshipClassesDialog(ManageItemsDialog):
    """A dialog to query user's preferences for updating relationship classes.

    Attributes:
        parent (TreeViewForm): data store widget
        kwargs_list (list): list of dictionaries corresponding to relationship classes to edit/update
    """
    def __init__(self, parent, kwargs_list):
        super().__init__(parent, kwargs_list)
        self.setWindowTitle("Edit relationship classes")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(LineEditDelegate(parent))
        self.table_view.horizontalHeader().setStretchLastSection(True)
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
        self.table_view.resizeColumnsToContents()
        self.connect_signals()

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


class EditRelationshipsDialog(ManageItemsDialog):
    """A dialog to query user's preferences for updating relationships.

    Attributes:
        parent (TreeViewForm): data store widget
        kwargs_list (list): list of dictionaries corresponding to relationships to edit/update
        relationship_class (KeyedTuple): the relationship class item (all edited relationships must be of this class)
    """
    def __init__(self, parent, kwargs_list, relationship_class):
        super().__init__(parent, kwargs_list)
        self.setWindowTitle("Edit relationships")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(AddRelationshipsDelegate(parent))
        self.table_view.horizontalHeader().setStretchLastSection(True)
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
        self.table_view.resizeColumnsToContents()
        self.connect_signals()

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


class ManageParameterTagsDialog(ManageItemsDialog):
    """A dialog to query user's preferences for managing parameter tags.

    Attributes:
        parent (TreeViewForm): data store widget
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Manage parameter tags")
        self.model = HybridTableModel(self)
        self.table_view.setItemDelegate(LineEditDelegate(parent))
        self.table_view.setModel(self.model)
        self.remove_row_icon = QIcon(":/icons/minus.png")
        self.orig_data = list()
        self.removed_id_list = list()
        self.id_list = list()
        model_data = list()
        for parameter_tag in self._parent.db_map.parameter_tag_list():
            try:
                self.id_list.append(parameter_tag.id)
            except KeyError:
                continue
            tag = parameter_tag.tag
            description = parameter_tag.description
            row_data = [tag, description]
            self.orig_data.append(row_data.copy())
            model_data.append(row_data)
        self.model.set_horizontal_header_labels(['parameter tag', 'description'])
        self.connect_signals()
        self.model.reset_model(model_data)
        self.table_view.resizeColumnsToContents()

    @Slot(name="_handle_model_reset")
    def _handle_model_reset(self):
        super()._handle_model_reset()
        column = self.model.columnCount() - 1
        for row in range(self.model.rowCount()):
            index = self.model.index(row, column)
            self.create_remove_row_button(index)

    def remove_clicked_row(self, button):
        column = self.model.columnCount() - 1
        for row in range(self.model.rowCount()):
            index = self.model.index(row, column)
            if button == self.table_view.indexWidget(index):
                self.model.removeRows(row, 1)
                try:
                    self.removed_id_list.append(self.id_list.pop(row))
                except IndexError:
                    pass
                break

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to update items."""
        # update
        items_to_update = list()
        for i in range(self.model.existing_item_model.rowCount()):
            id = self.id_list[i]
            tag, description = self.model.existing_item_model.row_data(i)
            if not tag:
                self._parent.msg_error.emit("Tag missing at row {}".format(i + 1))
                return
            orig_tag, orig_description = self.orig_data[i]
            if tag == orig_tag and description == orig_description:
                continue
            kwargs = {
                'id': id,
                'tag': tag,
                'description': description
            }
            items_to_update.append(kwargs)
        # insert
        items_to_add = list()
        for i in range(self.model.new_item_model.rowCount() - 1):  # last row will always be empty
            tag, description = self.model.new_item_model.row_data(i)
            if not tag:
                self._parent.msg_error.emit("Tag missing at row {0}".format(i + 1))
                return
            kwargs = {
                'tag': tag,
                'description': description
            }
            items_to_add.append(kwargs)
        try:
            if items_to_update:
                parameter_tags = self._parent.db_map.update_parameter_tags(*items_to_update)
                self._parent.update_parameter_tags(parameter_tags)
            if self.removed_id_list:
                self._parent.db_map.remove_items(parameter_tag_ids=self.removed_id_list)
                self._parent.remove_parameter_tags(self.removed_id_list)
            if items_to_add:
                parameter_tags = self._parent.db_map.add_parameter_tags(*items_to_add)
                self._parent.add_parameter_tags(parameter_tags)
            super().accept()
        except SpineIntegrityError as e:
            self._parent.msg_error.emit(e.msg)
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class CommitDialog(QDialog):
    """A dialog to query user's preferences for new commit.

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
        self.action_accept = QAction(self)
        self.action_accept.setShortcut(QApplication.translate("Dialog", "Ctrl+Return", None, -1))
        self.action_accept.triggered.connect(self.accept)
        self.action_accept.setEnabled(False)
        self.commit_msg_edit = QPlainTextEdit(self)
        self.commit_msg_edit.setPlaceholderText('Commit message \t(press Ctrl+Enter to commit)')
        self.commit_msg_edit.addAction(self.action_accept)
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
        self.action_accept.setEnabled(cond)
