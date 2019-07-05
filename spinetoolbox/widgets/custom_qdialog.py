######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

from PySide2.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QPlainTextEdit,
    QDialogButtonBox,
    QHeaderView,
    QAction,
    QApplication,
    QToolButton,
    QWidget,
    QLabel,
    QComboBox,
    QSpinBox,
    QStyle,
)
from PySide2.QtCore import Slot, Qt, QSize
from PySide2.QtGui import QIcon
from spinedb_api import SpineDBAPIError
from models import EmptyRowModel, MinimalTableModel, HybridTableModel
from widgets.custom_delegates import (
    AddObjectClassesDelegate,
    AddObjectsDelegate,
    AddRelationshipClassesDelegate,
    AddRelationshipsDelegate,
)
from widgets.custom_qtableview import CopyPasteTableView
from helpers import busy_effect, format_string_list


class ManageItemsDialog(QDialog):
    """A dialog with a CopyPasteTableView and a QDialogButtonBox, to be extended into
    dialogs to query user's preferences for adding/editing/managing data items

    Attributes:
        parent (TreeViewForm): data store widget
    """

    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent
        self.table_view = CopyPasteTableView(self)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setDefaultSectionSize(parent.default_row_height)
        self.button_box = QDialogButtonBox(self)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        layout = QVBoxLayout(self)
        layout.addWidget(self.table_view)
        layout.addWidget(self.button_box)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.table_view.itemDelegate().data_committed.connect(self._handle_data_committed)
        self.model.dataChanged.connect(self._handle_model_data_changed)

    def resize_window_to_columns(self):
        margins = self.layout().contentsMargins()
        self.resize(
            margins.left()
            + margins.right()
            + self.table_view.frameWidth() * 2
            + self.table_view.verticalHeader().width()
            + self.table_view.horizontalHeader().length(),
            400,
        )

    @Slot("QModelIndex", "QModelIndex", "QVector", name="_handle_model_data_changed")
    def _handle_model_data_changed(self, top_left, bottom_right, roles):
        """Reimplement in subclasses to handle changes in model data."""

    @Slot("QModelIndex", "QVariant", name='_handle_data_committed')
    def _handle_data_committed(self, index, data):
        """Update model data."""
        if data is None:
            return
        self.model.setData(index, data, Qt.EditRole)


class AddItemsDialog(ManageItemsDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.remove_rows_button = QToolButton()
        self.remove_rows_button.setToolTip("<p>Remove selected rows.</p>")
        self.layout().insertWidget(1, self.remove_rows_button)

    def connect_signals(self):
        super().connect_signals()
        self.remove_rows_button.clicked.connect(self.remove_selected_rows)

    @Slot("bool", name="remove_selected_rows")
    def remove_selected_rows(self, checked=True):
        indexes = self.table_view.selectedIndexes()
        rows = list(set(ind.row() for ind in indexes))
        for row in sorted(rows, reverse=True):
            self.model.removeRows(row, 1)


class AddObjectClassesDialog(AddItemsDialog):
    """A dialog to query user's preferences for new object classes.

    Attributes:
        parent (DataStoreForm): data store widget
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Add object classes")
        self.model = EmptyRowModel(self)
        self.table_view.setModel(self.model)
        self.combo_box = QComboBox(self)
        self.layout().insertWidget(0, self.combo_box)
        model = self._parent.object_tree_model
        # FIXME: This relies on the parent having the object tree
        self.object_class_items = [model.root_item.child(i, 0) for i in range(model.root_item.rowCount())]
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.table_view.setItemDelegate(AddObjectClassesDelegate(parent))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['object class name', 'description', 'display icon', 'databases'])
        db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in self._parent.db_maps])
        self.default_display_icon = self._parent.icon_mngr.default_display_icon()
        self.model.set_default_row(**{'databases': db_names, 'display icon': self.default_display_icon})
        self.model.clear()
        self.table_view.resizeColumnsToContents()
        self.resize_window_to_columns()
        insert_at_position_list = ['Insert new classes at the top']
        insert_at_position_list.extend(
            ["Insert new classes after '{}'".format(it.text()) for it in self.object_class_items]
        )
        self.combo_box.addItems(insert_at_position_list)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to add items."""
        object_class_d = dict()
        # Display order
        combo_index = self.combo_box.currentIndex()
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            name, description, display_icon, db_names = row_data
            db_name_list = db_names.split(",")
            try:
                db_maps = [self._parent.db_name_to_map[x] for x in db_name_list]
            except KeyError as e:
                self._parent.msg_error.emit("Invalid database {0} at row {1}".format(e, i + 1))
                return
            if not name:
                self._parent.msg_error.emit("Object class name missing at row {0}".format(i + 1))
                return
            if not display_icon:
                display_icon = self.default_display_icon
            item = {'name': name, 'description': description, 'display_icon': display_icon}
            for db_map in db_maps:
                if not self.object_class_items:
                    display_order = 0
                elif combo_index == 0:
                    # At the top
                    db_map_dict = self.object_class_items[0].data(Qt.UserRole + 1)
                    if db_map not in db_map_dict:
                        display_order = 0
                    else:
                        display_order = db_map_dict[db_map]['display_order'] - 1
                else:
                    # After the item
                    db_map_dict = self.object_class_items[combo_index - 1].data(Qt.UserRole + 1)
                    if db_map not in db_map_dict:
                        display_order = 0
                    else:
                        display_order = db_map_dict[db_map]['display_order']
                item['display_order'] = display_order
                object_class_d.setdefault(db_map, []).append(item)
        if not object_class_d:
            self._parent.msg_error.emit("Nothing to add")
            return
        self._parent.add_object_classes(object_class_d)
        super().accept()


class AddObjectsDialog(AddItemsDialog):
    """A dialog to query user's preferences for new objects.

    Attributes:
        parent (DataStoreForm): data store widget
        class_name (str): default object class name
        force_default (bool): if True, defaults are non-editable
    """

    def __init__(self, parent, db_maps=(), class_name=None, force_default=False):
        super().__init__(parent)
        default_db_maps = db_maps if db_maps else self._parent.db_maps
        self.setWindowTitle("Add objects")
        self.model = EmptyRowModel(self)
        self.model.force_default = force_default
        self.table_view.setModel(self.model)
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.table_view.setItemDelegate(AddObjectsDelegate(parent, self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['object class name', 'object name', 'description', 'databases'])
        self.obj_cls_dict = {
            db_map: {x.name: x.id for x in db_map.object_class_list()} for db_map in self._parent.db_maps
        }
        if class_name:
            default_db_maps = [db_map for db_map, names in self.obj_cls_dict.items() if class_name in names]
        else:
            default_db_maps = self._parent.db_maps
        db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in default_db_maps])
        self.model.set_default_row(**{'object class name': class_name, 'databases': db_names})
        self.model.clear()
        self.table_view.resizeColumnsToContents()
        self.resize_window_to_columns()

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
                icon = self._parent.icon_mngr.object_icon(object_class_name)
                self.model.setData(index, icon, Qt.DecorationRole)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to add items."""
        object_d = dict()
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            class_name, name, description, db_names = row_data
            if not name:
                self._parent.msg_error.emit("Object name missing at row {}".format(i + 1))
                return
            item = {'name': name, 'description': description}
            for db_name in db_names.split(","):
                if db_name not in self._parent.db_name_to_map:
                    self._parent.msg_error.emit("Invalid database {0} at row {1}".format(db_name, i + 1))
                    return
                db_map = self._parent.db_name_to_map[db_name]
                object_classes = self.obj_cls_dict[db_map]
                if class_name not in object_classes:
                    self._parent.msg_error.emit(
                        "Invalid object class '{}' for db '{}' at row {}".format(class_name, db_name, i + 1)
                    )
                    return
                class_id = object_classes[class_name]
                item['class_id'] = class_id
                object_d.setdefault(db_map, []).append(item)
        if not object_d:
            self._parent.msg_error.emit("Nothing to add")
            return
        self._parent.add_objects(object_d)
        super().accept()


class AddRelationshipClassesDialog(AddItemsDialog):
    """A dialog to query user's preferences for new relationship classes.

    Attributes:
        parent (DataStoreForm): data store widget
        db_maps (Iterable): DiffDatabaseMapping instances
        object_class_one_name (str): default object class name to put in first dimension
        force_default (bool): if True, defaults are non-editable
    """

    def __init__(self, parent, db_maps=(), object_class_one_name=None, force_default=False):
        super().__init__(parent)
        self.setWindowTitle("Add relationship classes")
        self.model = EmptyRowModel(self)
        self.model.force_default = force_default
        self.table_view.setModel(self.model)
        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.addWidget(QLabel("Number of dimensions"))
        self.spin_box = QSpinBox(self)
        self.spin_box.setMinimum(1)
        layout.addWidget(self.spin_box)
        layout.addStretch()
        self.layout().insertWidget(0, widget)
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cubes_minus.svg"))
        self.table_view.setItemDelegate(AddRelationshipClassesDelegate(parent, self))
        self.number_of_dimensions = 1
        self.connect_signals()
        self.model.set_horizontal_header_labels(['object class 1 name', 'relationship class name', 'databases'])
        self.obj_cls_dict = {
            db_map: {x.name: x.id for x in db_map.object_class_list()} for db_map in self._parent.db_maps
        }
        if object_class_one_name:
            default_db_maps = [db_map for db_map, names in self.obj_cls_dict.items() if object_class_one_name in names]
        else:
            default_db_maps = self._parent.db_maps
        db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in default_db_maps])
        self.model.set_default_row(**{'object class 1 name': object_class_one_name, 'databases': db_names})
        self.model.clear()
        self.table_view.resizeColumnsToContents()
        self.resize_window_to_columns()

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        self.spin_box.valueChanged.connect(self._handle_spin_box_value_changed)

    @Slot("int", name="_handle_spin_box_value_changed")
    def _handle_spin_box_value_changed(self, i):
        self.spin_box.setEnabled(False)
        if i > self.number_of_dimensions:
            self.insert_column()
        elif i < self.number_of_dimensions:
            self.remove_column()
        self.spin_box.setEnabled(True)
        self.resize_window_to_columns()

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
                    break
                index = self.model.index(row, column)
                object_class_name = index.data(Qt.DisplayRole)
                if not object_class_name:
                    continue
                icon = self._parent.icon_mngr.object_icon(object_class_name)
                self.model.setData(index, icon, Qt.DecorationRole)
            else:
                col_data = lambda j: self.model.index(row, j).data()
                obj_cls_names = [col_data(j) for j in range(self.number_of_dimensions) if col_data(j)]
                if len(obj_cls_names) == 1:
                    relationship_class_name = obj_cls_names[0] + "__"
                else:
                    relationship_class_name = "__".join(obj_cls_names)
                self.model.setData(self.model.index(row, self.number_of_dimensions), relationship_class_name)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to add items."""
        rel_cls_d = dict()
        name_column = self.model.horizontal_header_labels().index("relationship class name")
        db_column = self.model.horizontal_header_labels().index("databases")
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            relationship_class_name = row_data[name_column]
            if not relationship_class_name:
                self._parent.msg_error.emit("Relationship class name missing at row {}".format(i + 1))
                return
            item = {'name': relationship_class_name}
            db_names = row_data[db_column]
            for db_name in db_names.split(","):
                if db_name not in self._parent.db_name_to_map:
                    self._parent.msg_error.emit("Invalid database {0} at row {1}".format(db_name, i + 1))
                    return
                db_map = self._parent.db_name_to_map[db_name]
                object_classes = self.obj_cls_dict[db_map]
                object_class_id_list = list()
                for column in range(name_column):  # Leave 'name' column outside
                    object_class_name = row_data[column]
                    if object_class_name not in object_classes:
                        self._parent.msg_error.emit(
                            "Invalid object class '{}' for db '{}' at row {}".format(class_name, db_name, i + 1)
                        )
                        return
                    object_class_id = object_classes[object_class_name]
                    object_class_id_list.append(object_class_id)
                item['object_class_id_list'] = object_class_id_list
                rel_cls_d.setdefault(db_map, []).append(item)
        if not rel_cls_d:
            self._parent.msg_error.emit("Nothing to add")
            return
        self._parent.add_relationship_classes(rel_cls_d)
        super().accept()


class AddRelationshipsDialog(AddItemsDialog):
    """A dialog to query user's preferences for new relationships.

    Attributes:
        parent (DataStoreForm): data store widget
        relationship_class_key (tuple): (name, object_class_name_list) for identifying the relationship class
        object_name (str): default object name
        object_class_name (str): default object class name
        force_default (bool): if True, defaults are non-editable
    """

    def __init__(
        self, parent, relationship_class_key=None, object_class_name=None, object_name=None, force_default=False
    ):
        super().__init__(parent)
        self.default_object_class_name = object_class_name
        self.default_object_name = object_name
        self.relationship_class = None
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
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cubes_minus.svg"))
        self.obj_dict = {
            db_map: {(x.class_id, x.name): x.id for x in db_map.object_list()} for db_map in self._parent.db_maps
        }
        self.rel_cls_dict = {
            db_map: {
                (x.name, x.object_class_name_list): (x.id, x.object_class_id_list)
                for x in db_map.wide_relationship_class_list()
            }
            for db_map in self._parent.db_maps
        }
        combo_items = {x: None for rel_cls_list in self.rel_cls_dict.values() for x in rel_cls_list}
        combo_items = list(combo_items)
        self.combo_box.addItems(["{0} ({1})".format(*key) for key in combo_items])
        self.table_view.setItemDelegate(AddRelationshipsDelegate(parent, self))
        if relationship_class_key in combo_items:
            current_index = combo_items.index(relationship_class_key)
            self.combo_box.setCurrentIndex(current_index)
            self.reset_model(*relationship_class_key)
        else:
            self.combo_box.setCurrentIndex(-1)
        self.connect_signals()
        self.combo_box.setEnabled(not force_default)

    def connect_signals(self):
        """Connect signals to slots."""
        self.combo_box.currentTextChanged.connect(self.call_reset_model)
        super().connect_signals()

    @Slot("str", name='call_reset_model')
    def call_reset_model(self, text):
        """Called when relationship class's combobox's index changes.
        Update relationship_class attribute accordingly and reset model."""
        class_name, object_class_name_list = text.split(" ")
        self.reset_model(class_name, object_class_name_list[1:-1])

    def reset_model(self, class_name, object_class_name_list):
        """Setup model according to current relationship class selected in combobox
        (or given as input).
        """
        default_db_maps = [
            db_map
            for db_map, rel_cls_list in self.rel_cls_dict.items()
            if (class_name, object_class_name_list) in rel_cls_list
        ]
        object_class_name_list = object_class_name_list.split(',')
        db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in default_db_maps])
        header = [*[x + " name" for x in object_class_name_list], 'relationship name', 'databases']
        self.model.set_horizontal_header_labels(header)
        defaults = {'databases': db_names}
        if self.default_object_name and self.default_object_class_name:
            columns = [j for j, x in enumerate(object_class_name_list) if x == self.default_object_class_name]
            defaults.update({header[j]: self.default_object_name for j in columns})
        self.model.set_default_row(**defaults)
        self.model.clear()
        self.table_view.resizeColumnsToContents()
        self.resize_window_to_columns()

    @Slot("QModelIndex", "QModelIndex", "QVector", name="_handle_model_data_changed")
    def _handle_model_data_changed(self, top_left, bottom_right, roles):
        if Qt.EditRole not in roles:
            return
        header = self.model.horizontal_header_labels()
        top = top_left.row()
        left = top_left.column()
        bottom = bottom_right.row()
        right = bottom_right.column()
        number_of_dimensions = self.model.columnCount() - 2
        for row in range(top, bottom + 1):
            if header.index('relationship name') not in range(left, right + 1):
                col_data = lambda j: self.model.index(row, j).data()
                obj_names = [col_data(j) for j in range(number_of_dimensions) if col_data(j)]
                if len(obj_names) == 1:
                    relationship_name = obj_names[0] + "__"
                else:
                    relationship_name = "__".join(obj_names)
                self.model.setData(self.model.index(row, number_of_dimensions), relationship_name)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to add items."""
        class_name, object_class_name_list = self.combo_box.currentText().split(" ")
        object_class_name_list = object_class_name_list[1:-1]
        relationship_d = dict()
        name_column = self.model.horizontal_header_labels().index("relationship name")
        db_column = self.model.horizontal_header_labels().index("databases")
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            object_name_list = [row_data[column] for column in range(name_column)]
            relationship_name = row_data[name_column]
            if not relationship_name:
                self._parent.msg_error.emit("Relationship name missing at row {}".format(i + 1))
                return
            item = {'name': relationship_name}
            db_names = row_data[db_column]
            for db_name in db_names.split(","):
                if db_name not in self._parent.db_name_to_map:
                    self._parent.msg_error.emit("Invalid database {0} at row {1}".format(db_name, i + 1))
                    return
                db_map = self._parent.db_name_to_map[db_name]
                relationship_classes = self.rel_cls_dict[db_map]
                if (class_name, object_class_name_list) not in relationship_classes:
                    self._parent.msg_error.emit(
                        "Invalid relationship class '{}' for db '{}' at row {}".format(class_name, db_name, i + 1)
                    )
                    return
                class_id, object_class_id_list = relationship_classes[class_name, object_class_name_list]
                object_class_id_list = [int(x) for x in object_class_id_list.split(",")]
                objects = self.obj_dict[db_map]
                object_id_list = list()
                for object_class_id, object_name in zip(object_class_id_list, object_name_list):
                    if (object_class_id, object_name) not in objects:
                        self._parent.msg_error.emit(
                            "Invalid object '{}' for db '{}' at row {}".format(object_name, db_name, i + 1)
                        )
                        return
                    object_id = objects[object_class_id, object_name]
                    object_id_list.append(object_id)
                item.update({'object_id_list': object_id_list, 'class_id': class_id})
                relationship_d.setdefault(db_map, []).append(item)
        if not relationship_d:
            self._parent.msg_error.emit("Nothing to add")
            return
        self._parent.add_relationships(relationship_d)
        super().accept()


class EditItemsDialog(ManageItemsDialog):
    def __init__(self, parent):
        super().__init__(parent)

    @Slot(name="_handle_model_reset")
    def _handle_model_reset(self):
        """Resize columns and form."""
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.resizeColumnsToContents()
        self.resize_window_to_columns()


class EditObjectClassesDialog(EditItemsDialog):
    """A dialog to query user's preferences for updating object classes.

    Attributes:
        parent (TreeViewForm): data store widget
        kwargs_list (list): list of dictionaries corresponding to object classes to edit/update
    """

    def __init__(self, parent, kwargs_list):
        super().__init__(parent)
        self.setWindowTitle("Edit object classes")
        self.model = MinimalTableModel(self)
        self.model.set_horizontal_header_labels(['object class name', 'description', 'display_icon'])
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(LineEditDelegate(parent))
        self.table_view.setItemDelegateForColumn(2, IconColorDialogDelegate(parent))
        self.connect_signals()
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
            try:
                display_icon = kwargs["display_icon"]
            except KeyError:
                display_icon = None
            row_data = [name, description, display_icon]
            self.orig_data.append(row_data.copy())
            model_data.append(row_data)
        self.model.reset_model(model_data)

    def connect_signals(self):
        super().connect_signals()
        self.table_view.itemDelegateForColumn(2).data_committed.connect(self._handle_data_committed)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to update items."""
        kwargs_list = list()
        for i in range(self.model.rowCount()):
            id = self.id_list[i]
            name, description, display_icon = self.model.row_data(i)
            if not name:
                self._parent.msg_error.emit("Object class name missing at row {}".format(i + 1))
                return
            orig_name, orig_description, orig_display_icon = self.orig_data[i]
            if name == orig_name and description == orig_description and display_icon == orig_display_icon:
                continue
            kwargs = {
                'id': id,
                'name': name,
                'description': description,
                'display_icon': int(display_icon) if display_icon else self.parent().icon_mngr.default_display_icon(),
            }
            kwargs_list.append(kwargs)
        if not kwargs_list:
            self._parent.msg_error.emit("Nothing to update")
            return
        try:
            object_classes, error_log = self._parent.db_map.update_object_classes(*kwargs_list)
            self._parent.update_object_classes(object_classes)
            if error_log:
                self._parent.msg_error.emit(format_string_list(error_log))
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
        super().__init__(parent)
        self.setWindowTitle("Edit objects")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(LineEditDelegate(parent))
        self.connect_signals()
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
            kwargs = {'id': id, 'name': name, 'description': description}
            kwargs_list.append(kwargs)
        if not kwargs_list:
            self._parent.msg_error.emit("Nothing to update")
            return
        try:
            objects, error_log = self._parent.db_map.update_objects(*kwargs_list)
            self._parent.update_objects(objects)
            if error_log:
                self._parent.msg_error.emit(format_string_list(error_log))
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
        super().__init__(parent)
        self.setWindowTitle("Edit relationship classes")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(LineEditDelegate(parent))
        self.connect_signals()
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
            kwargs = {'id': id, 'name': name}
            kwargs_list.append(kwargs)
        if not kwargs_list:
            self._parent.msg_error.emit("Nothing to update")
            return
        try:
            wide_relationship_classes, error_log = self._parent.db_map.update_wide_relationship_classes(*kwargs_list)
            self._parent.update_relationship_classes(wide_relationship_classes)
            if error_log:
                self._parent.msg_error.emit(format_string_list(error_log))
            super().accept()
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class EditRelationshipsDialog(EditItemsDialog):
    """A dialog to query user's preferences for updating relationships.

    Attributes:
        parent (TreeViewForm): data store widget
        kwargs_list (list): list of dictionaries corresponding to relationships to edit/update
        relationship_class (dict): the relationship class item (all edited relationships must be of this class)
    """

    def __init__(self, parent, kwargs_list, relationship_class):
        super().__init__(parent)
        self.setWindowTitle("Edit relationships")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(AddRelationshipsDelegate(parent))
        self.connect_signals()
        object_class_name_list = relationship_class['object_class_name_list'].split(",")
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
                object_ = self._parent.db_map.object_list().filter_by(name=object_name).one_or_none()
                if not object_:
                    self._parent.msg_error.emit("Couldn't find object '{}' at row {}".format(object_name, i + 1))
                    return
                object_id_list.append(object_.id)
            if orig_relationship_name == relationship_name and orig_object_id_list == object_id_list:
                continue
            kwargs = {'id': id, 'name': relationship_name, 'object_id_list': object_id_list}
            kwargs_list.append(kwargs)
        if not kwargs_list:
            self._parent.msg_error.emit("Nothing to update")
            return
        try:
            wide_relationships, error_log = self._parent.db_map.update_wide_relationships(*kwargs_list)
            self._parent.update_relationships(wide_relationships)
            if error_log:
                self._parent.msg_error.emit(format_string_list(error_log))
            super().accept()
        except SpineDBAPIError as e:
            self._parent.msg_error.emit(e.msg)


class ManageParameterTagsDialog(AddItemsDialog):
    """A dialog to query user's preferences for managing parameter tags.

    Attributes:
        parent (TreeViewForm): data store widget
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Manage parameter tags")
        self.model = HybridTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(LineEditDelegate(parent))
        self.connect_signals()
        self.remove_row_icon = QIcon(":/icons/minus.svg")
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
        self.model.reset_model(model_data)

    @Slot(name="_handle_model_reset")
    def _handle_model_reset(self):
        """Call parent method, and then create remove row buttons for initial rows."""
        super()._handle_model_reset()
        column = self.model.columnCount() - 1
        for row in range(self.model.rowCount()):
            index = self.model.index(row, column)
            button = self.create_remove_row_button(index)
            self.table_view.setIndexWidget(index, button)

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
            kwargs = {'id': id, 'tag': tag, 'description': description}
            items_to_update.append(kwargs)
        # insert
        items_to_add = list()
        for i in range(self.model.new_item_model.rowCount() - 1):  # last row will always be empty
            tag, description = self.model.new_item_model.row_data(i)
            if not tag:
                self._parent.msg_error.emit("Tag missing at row {0}".format(i + 1))
                return
            kwargs = {'tag': tag, 'description': description}
            items_to_add.append(kwargs)
        error_log = list()
        try:
            if items_to_update:
                parameter_tags, upd_error_log = self._parent.db_map.update_parameter_tags(*items_to_update)
                error_log += upd_error_log
                self._parent.update_parameter_tags(parameter_tags)
            if self.removed_id_list:
                self._parent.db_map.remove_items(parameter_tag_ids=self.removed_id_list)
                self._parent.remove_parameter_tags(self.removed_id_list)
            if items_to_add:
                parameter_tags, add_error_log = self._parent.db_map.add_parameter_tags(*items_to_add)
                error_log += add_error_log
                self._parent.add_parameter_tags(parameter_tags)
            if error_log:
                self._parent.msg_error.emit(format_string_list(error_log))
            super().accept()
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
