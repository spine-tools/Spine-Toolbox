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
    QCheckBox,
)
from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QIcon
from models import EmptyRowModel, MinimalTableModel, HybridTableModel
from widgets.custom_delegates import (
    ManageObjectClassesDelegate,
    ManageObjectsDelegate,
    ManageRelationshipClassesDelegate,
    ManageRelationshipsDelegate,
    RemoveTreeItemsDelegate,
    ManageParameterTagsDelegate,
)
from widgets.custom_qtableview import CopyPasteTableView
from helpers import busy_effect


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
        self.model.modelReset.connect(self._handle_model_reset)

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

    @Slot(name="_handle_model_reset")
    def _handle_model_reset(self):
        """Resize columns and form."""
        self.table_view.resizeColumnsToContents()
        self.resize_window_to_columns()


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

    def all_databases(self, row):
        """Returns a list of db names available for a given row.
        Used by delegates.
        """
        return [self._parent.db_map_to_name[db_map] for db_map in self._parent.db_maps]


class GetObjectClassesMixin:
    """Provides a method to retrieve object classes for AddObjectsDialog and AddRelationshipClassesDialog.
    """

    def object_class_name_list(self, row):
        """Return a list of object class names present in all databases selected for given row.
        Used by `ManageObjectsDelegate`.
        """
        db_column = self.model.header.index('databases')
        db_names = self.model._main_data[row][db_column]
        db_name_to_map = self._parent.db_name_to_map
        db_maps = iter(db_name_to_map[x] for x in db_names.split(",") if x in db_name_to_map)
        db_map = next(db_maps, None)
        if not db_map:
            return []
        # Initalize list from first db_map
        object_class_name_list = list(self.obj_cls_dict[db_map])
        # Update list from remaining db_maps
        for db_map in db_maps:
            object_class_name_list = [x for x in self.obj_cls_dict[db_map] if x in object_class_name_list]
        return object_class_name_list


class GetObjectsMixin:
    """Provides a method to retrieve objects for AddRelationshipsDialog and EditRelationshipsDialog.
    """

    def object_name_list(self, row, column):
        """Return a list of object names present in all databases selected for given row.
        Used by `ManageRelationshipsDelegate`.
        """
        db_column = self.model.header.index('databases')
        db_names = self.model._main_data[row][db_column]
        db_name_to_map = self._parent.db_name_to_map
        db_maps = iter(db_name_to_map[x] for x in db_names.split(",") if x in db_name_to_map)
        db_map = next(db_maps, None)
        if not db_map:
            return []
        # Initalize list from first db_map
        relationship_classes = self.rel_cls_dict[db_map]
        rel_cls_key = (self.class_name, self.object_class_name_list)
        if rel_cls_key not in relationship_classes:
            return []
        _, object_class_id_list = relationship_classes[rel_cls_key]
        object_class_id_list = [int(x) for x in object_class_id_list.split(",")]
        object_class_id = object_class_id_list[column]
        objects = self.obj_dict[db_map]
        object_name_list = [name for (class_id, name) in objects if class_id == object_class_id]
        # Update list from remaining db_maps
        for db_map in db_maps:
            relationship_classes = self.rel_cls_dict[db_map]
            if rel_cls_key not in relationship_classes:
                continue
            _, object_class_id_list = relationship_classes[rel_cls_key]
            object_class_id_list = [int(x) for x in object_class_id_list.split(",")]
            object_class_id = object_class_id_list[column]
            objects = self.obj_dict[db_map]
            object_name_list = [
                name for (class_id, name) in objects if class_id == object_class_id and name in object_name_list
            ]
        return object_name_list


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
        self.obj_cls_dict = {
            db_map: {x.name: x.display_order for x in db_map.object_class_list()} for db_map in self._parent.db_maps
        }
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.table_view.setItemDelegate(ManageObjectClassesDelegate(self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['object class name', 'description', 'display icon', 'databases'])
        db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in self._parent.db_maps])
        self.default_display_icon = self._parent.icon_mngr.default_display_icon()
        self.model.set_default_row(**{'databases': db_names, 'display icon': self.default_display_icon})
        self.model.clear()
        insert_at_position_list = ['Insert new classes at the top']
        object_class_names = {x: None for db_map in self._parent.db_maps for x in self.obj_cls_dict[db_map]}
        self.object_class_names = list(object_class_names)
        insert_at_position_list.extend(
            ["Insert new classes after '{}'".format(name) for name in self.object_class_names]
        )
        self.combo_box.addItems(insert_at_position_list)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to add items."""
        object_class_d = dict()
        # Display order
        combo_index = self.combo_box.currentIndex()
        after_obj_cls = self.object_class_names[combo_index - 1] if combo_index > 0 else None
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
            pre_item = {'name': name, 'description': description, 'display_icon': display_icon}
            for db_map in db_maps:
                obj_cls_order = self.obj_cls_dict[db_map]
                if not obj_cls_order:
                    # This happens when there's no object classes in the db
                    display_order = 0
                elif after_obj_cls is None:
                    # At the top
                    display_order = list(obj_cls_order.values())[0] - 1
                else:
                    display_order = obj_cls_order[after_obj_cls]
                item = pre_item.copy()
                item['display_order'] = display_order
                object_class_d.setdefault(db_map, []).append(item)
        if not object_class_d:
            self._parent.msg_error.emit("Nothing to add")
            return
        self._parent.add_object_classes(object_class_d)
        super().accept()


class AddObjectsDialog(AddItemsDialog, GetObjectClassesMixin):
    """A dialog to query user's preferences for new objects.

    Attributes:
        parent (DataStoreForm): data store widget
        class_name (str): default object class name
        force_default (bool): if True, defaults are non-editable
    """

    def __init__(self, parent, class_name=None, force_default=False):
        super().__init__(parent)
        self.setWindowTitle("Add objects")
        self.model = EmptyRowModel(self)
        self.model.force_default = force_default
        self.table_view.setModel(self.model)
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.table_view.setItemDelegate(ManageObjectsDelegate(self))
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
            pre_item = {'name': name, 'description': description}
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
                item = pre_item.copy()
                item['class_id'] = class_id
                object_d.setdefault(db_map, []).append(item)
        if not object_d:
            self._parent.msg_error.emit("Nothing to add")
            return
        self._parent.add_objects(object_d)
        super().accept()


class AddRelationshipClassesDialog(AddItemsDialog, GetObjectClassesMixin):
    """A dialog to query user's preferences for new relationship classes.

    Attributes:
        parent (DataStoreForm): data store widget
        object_class_one_name (str): default object class name to put in first dimension
        force_default (bool): if True, defaults are non-editable
    """

    def __init__(self, parent, object_class_one_name=None, force_default=False):
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
        self.table_view.setItemDelegate(ManageRelationshipClassesDelegate(self))
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
                col_data = lambda j: self.model.index(row, j).data()  # pylint: disable=cell-var-from-loop
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
            pre_item = {'name': relationship_class_name}
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
                            "Invalid object class '{}' for db '{}' at row {}".format(object_class_name, db_name, i + 1)
                        )
                        return
                    object_class_id = object_classes[object_class_name]
                    object_class_id_list.append(object_class_id)
                item = pre_item.copy()
                item['object_class_id_list'] = object_class_id_list
                rel_cls_d.setdefault(db_map, []).append(item)
        if not rel_cls_d:
            self._parent.msg_error.emit("Nothing to add")
            return
        self._parent.add_relationship_classes(rel_cls_d)
        super().accept()


class AddRelationshipsDialog(AddItemsDialog, GetObjectsMixin):
    """A dialog to query user's preferences for new relationships.

    Attributes:
        parent (DataStoreForm): data store widget
        relationship_class_key (tuple): (class_name, object_class_name_list) for identifying the relationship class
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
        self.table_view.setItemDelegate(ManageRelationshipsDelegate(self))
        self.connect_signals()
        if relationship_class_key in combo_items:
            current_index = combo_items.index(relationship_class_key)
            self.combo_box.setCurrentIndex(current_index)
            self.class_name, self.object_class_name_list = relationship_class_key
            self.reset_model()
        else:
            self.combo_box.setCurrentIndex(-1)
        self.combo_box.setEnabled(not force_default)

    def connect_signals(self):
        """Connect signals to slots."""
        self.combo_box.currentTextChanged.connect(self.call_reset_model)
        super().connect_signals()

    @Slot("str", name='call_reset_model')
    def call_reset_model(self, text):
        """Called when relationship class's combobox's index changes.
        Update relationship_class attribute accordingly and reset model."""
        self.class_name, self.object_class_name_list = text.split(" ")
        self.object_class_name_list = self.object_class_name_list[1:-1]
        self.reset_model()

    def reset_model(self):
        """Setup model according to current relationship class selected in combobox.
        """
        default_db_maps = [
            db_map
            for db_map, rel_cls_list in self.rel_cls_dict.items()
            if (self.class_name, self.object_class_name_list) in rel_cls_list
        ]
        object_class_name_list = self.object_class_name_list.split(',')
        db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in default_db_maps])
        header = [*[x + " name" for x in object_class_name_list], 'relationship name', 'databases']
        self.model.set_horizontal_header_labels(header)
        defaults = {'databases': db_names}
        if self.default_object_name and self.default_object_class_name:
            columns = [j for j, x in enumerate(object_class_name_list) if x == self.default_object_class_name]
            defaults.update({header[j]: self.default_object_name for j in columns})
        self.model.set_default_row(**defaults)
        self.model.clear()

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
                col_data = lambda j: self.model.index(row, j).data()  # pylint: disable=cell-var-from-loop
                obj_names = [col_data(j) for j in range(number_of_dimensions) if col_data(j)]
                if len(obj_names) == 1:
                    relationship_name = obj_names[0] + "__"
                else:
                    relationship_name = "__".join(obj_names)
                self.model.setData(self.model.index(row, number_of_dimensions), relationship_name)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to add items."""
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
            pre_item = {'name': relationship_name}
            db_names = row_data[db_column]
            for db_name in db_names.split(","):
                if db_name not in self._parent.db_name_to_map:
                    self._parent.msg_error.emit("Invalid database {0} at row {1}".format(db_name, i + 1))
                    return
                db_map = self._parent.db_name_to_map[db_name]
                relationship_classes = self.rel_cls_dict[db_map]
                if (self.class_name, self.object_class_name_list) not in relationship_classes:
                    self._parent.msg_error.emit(
                        "Invalid relationship class '{}' for db '{}' at row {}".format(self.class_name, db_name, i + 1)
                    )
                    return
                class_id, object_class_id_list = relationship_classes[self.class_name, self.object_class_name_list]
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
                item = pre_item.copy()
                item.update({'object_id_list': object_id_list, 'class_id': class_id})
                relationship_d.setdefault(db_map, []).append(item)
        if not relationship_d:
            self._parent.msg_error.emit("Nothing to add")
            return
        self._parent.add_relationships(relationship_d)
        super().accept()


class EditOrRemoveItemsDialog(ManageItemsDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.db_map_dicts = list()

    def all_databases(self, row):
        """Returns a list of db names available for a given row.
        Used by delegates.
        """
        return [self._parent.db_map_to_name[db_map] for db_map in self.db_map_dicts[row]]


class EditObjectClassesDialog(EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for updating object classes.

    Attributes:
        parent (DataStoreForm): data store widget
        db_map_dicts (list): list of dictionaries mapping dbs to object classes for editing
    """

    def __init__(self, parent, db_map_dicts):
        super().__init__(parent)
        self.setWindowTitle("Edit object classes")
        self.model = MinimalTableModel(self)
        self.model.set_horizontal_header_labels(['object class name', 'description', 'display icon', 'databases'])
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageObjectClassesDelegate(self))
        self.connect_signals()
        self.orig_data = list()
        self.default_display_icon = self._parent.icon_mngr.default_display_icon()
        model_data = list()
        for db_map_dict in db_map_dicts:
            db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in db_map_dict])
            item = list(db_map_dict.values())[0]
            name = item.get('name')
            if not name:
                continue
            description = item.get('description')
            display_icon = item.get('display_icon')
            row_data = [name, description, display_icon]
            self.orig_data.append(row_data.copy())
            row_data.append(db_names)
            model_data.append(row_data)
            self.db_map_dicts.append(db_map_dict)
        self.model.reset_model(model_data)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to update items."""
        object_class_d = dict()
        for i in range(self.model.rowCount()):
            name, description, display_icon, db_names = self.model.row_data(i)
            db_name_list = db_names.split(",")
            try:
                db_maps = [self._parent.db_name_to_map[x] for x in db_name_list]
            except KeyError as e:
                self._parent.msg_error.emit("Invalid database {0} at row {1}".format(e, i + 1))
                return
            if not name:
                self._parent.msg_error.emit("Object class name missing at row {}".format(i + 1))
                return
            orig_row = self.orig_data[i]
            if [name, description, display_icon] == orig_row:
                continue
            if not display_icon:
                display_icon = self.default_display_icon
            pre_item = {'name': name, 'description': description, 'display_icon': display_icon}
            for db_map in db_maps:
                id_ = self.db_map_dicts[i][db_map]['id']
                item = pre_item.copy()
                item['id'] = id_
                object_class_d.setdefault(db_map, []).append(item)
        if not object_class_d:
            self._parent.msg_error.emit("Nothing to update")
            return
        self._parent.update_object_classes(object_class_d)
        super().accept()


class EditObjectsDialog(EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for updating objects.

    Attributes:
        parent (DataStoreForm): data store widget
        db_map_dicts (list): list of dictionaries mapping dbs to objects for editing
    """

    def __init__(self, parent, db_map_dicts):
        super().__init__(parent)
        self.setWindowTitle("Edit objects")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageObjectsDelegate(self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['object name', 'description', 'databases'])
        self.orig_data = list()
        model_data = list()
        for db_map_dict in db_map_dicts:
            db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in db_map_dict])
            item = list(db_map_dict.values())[0]
            name = item.get('name')
            if not name:
                continue
            description = item.get('description')
            row_data = [name, description]
            self.orig_data.append(row_data.copy())
            row_data.append(db_names)
            model_data.append(row_data)
            self.db_map_dicts.append(db_map_dict)
        self.model.reset_model(model_data)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to update items."""
        object_d = dict()
        for i in range(self.model.rowCount()):
            name, description, db_names = self.model.row_data(i)
            db_name_list = db_names.split(",")
            try:
                db_maps = [self._parent.db_name_to_map[x] for x in db_name_list]
            except KeyError as e:
                self._parent.msg_error.emit("Invalid database {0} at row {1}".format(e, i + 1))
                return
            if not name:
                self._parent.msg_error.emit("Object name missing at row {}".format(i + 1))
                return
            orig_row = self.orig_data[i]
            if [name, description] == orig_row:
                continue
            pre_item = {'name': name, 'description': description}
            for db_map in db_maps:
                id_ = self.db_map_dicts[i][db_map]['id']
                item = pre_item.copy()
                item['id'] = id_
                object_d.setdefault(db_map, []).append(item)
        if not object_d:
            self._parent.msg_error.emit("Nothing to update")
            return
        self._parent.update_objects(object_d)
        super().accept()


class EditRelationshipClassesDialog(EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for updating relationship classes.

    Attributes:
        parent (DataStoreForm): data store widget
        db_map_dicts (list): list of dictionaries mapping dbs to relationship classes for editing
    """

    def __init__(self, parent, db_map_dicts):
        super().__init__(parent)
        self.setWindowTitle("Edit relationship classes")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageRelationshipClassesDelegate(self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['relationship class name', 'databases'])
        self.orig_data = list()
        model_data = list()
        for db_map_dict in db_map_dicts:
            db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in db_map_dict])
            item = list(db_map_dict.values())[0]
            name = item.get('name')
            if not name:
                continue
            row_data = [name]
            self.orig_data.append(row_data.copy())
            row_data.append(db_names)
            model_data.append(row_data)
            self.db_map_dicts.append(db_map_dict)
        self.model.reset_model(model_data)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to update items."""
        rel_cls_d = dict()
        for i in range(self.model.rowCount()):
            name, db_names = self.model.row_data(i)
            db_name_list = db_names.split(",")
            try:
                db_maps = [self._parent.db_name_to_map[x] for x in db_name_list]
            except KeyError as e:
                self._parent.msg_error.emit("Invalid database {0} at row {1}".format(e, i + 1))
                return
            if not name:
                self._parent.msg_error.emit("Relationship class name missing at row {}".format(i + 1))
                return
            orig_row = self.orig_data[i]
            if [name] == orig_row:
                continue
            pre_item = {'name': name}
            for db_map in db_maps:
                id_ = self.db_map_dicts[i][db_map]['id']
                item = pre_item.copy()
                item['id'] = id_
                rel_cls_d.setdefault(db_map, []).append(item)
        if not rel_cls_d:
            self._parent.msg_error.emit("Nothing to update")
            return
        self._parent.update_relationship_classes(rel_cls_d)
        super().accept()


class EditRelationshipsDialog(EditOrRemoveItemsDialog, GetObjectsMixin):
    """A dialog to query user's preferences for updating relationships.

    Attributes:
        parent (DataStoreForm): data store widget
        db_map_dicts (list): list of dictionaries mapping dbs to relationships for editing
        ref_class_key (tuple): (class_name, object_class_name_list) for identifying the relationship class
    """

    def __init__(self, parent, db_map_dicts, ref_class_key):
        super().__init__(parent)
        self.setWindowTitle("Edit relationships")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageRelationshipsDelegate(self))
        self.connect_signals()
        self.class_name, self.object_class_name_list = ref_class_key
        object_class_name_list = self.object_class_name_list.split(",")
        self.model.set_horizontal_header_labels(
            [x + ' name' for x in object_class_name_list] + ['relationship name', 'databases']
        )
        self.orig_data = list()
        model_data = list()
        db_maps = set()
        for db_map_dict in db_map_dicts:
            db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in db_map_dict])
            db_maps.update(db_map_dict.keys())
            item = list(db_map_dict.values())[0]
            name = item.get('name')
            object_name_list = item.get("object_name_list")
            if not name or not object_name_list:
                continue
            object_name_list = object_name_list.split(",")
            row_data = [*object_name_list, name]
            self.orig_data.append(row_data.copy())
            row_data.append(db_names)
            model_data.append(row_data)
            self.db_map_dicts.append(db_map_dict)
        self.model.reset_model(model_data)
        self.obj_dict = {db_map: {(x.class_id, x.name): x.id for x in db_map.object_list()} for db_map in db_maps}
        self.rel_cls_dict = {
            db_map: {
                (x.name, x.object_class_name_list): (x.id, x.object_class_id_list)
                for x in db_map.wide_relationship_class_list()
            }
            for db_map in db_maps
        }

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to update items."""
        relationship_d = dict()
        name_column = self.model.horizontal_header_labels().index("relationship name")
        db_column = self.model.horizontal_header_labels().index("databases")
        for i in range(self.model.rowCount()):
            row_data = self.model.row_data(i)
            object_name_list = [row_data[column] for column in range(name_column)]
            name = row_data[name_column]
            if not name:
                self._parent.msg_error.emit("Relationship name missing at row {}".format(i + 1))
                return
            db_names = row_data[db_column]
            db_name_list = db_names.split(",")
            try:
                db_maps = [self._parent.db_name_to_map[x] for x in db_name_list]
            except KeyError as e:
                self._parent.msg_error.emit("Invalid database {0} at row {1}".format(e, i + 1))
                return
            if not name:
                self._parent.msg_error.emit("Relationship class name missing at row {}".format(i + 1))
                return
            orig_row = self.orig_data[i]
            if [*object_name_list, name] == orig_row:
                continue
            pre_item = {'name': name}
            for db_map in db_maps:
                id_ = self.db_map_dicts[i][db_map]['id']
                # Find object_class_id_list
                relationship_classes = self.rel_cls_dict[db_map]
                if (self.class_name, self.object_class_name_list) not in relationship_classes:
                    self._parent.msg_error.emit(
                        "Invalid relationship class '{}' for db '{}' at row {}".format(self.class_name, db_name, i + 1)
                    )
                    return
                _, object_class_id_list = relationship_classes[self.class_name, self.object_class_name_list]
                object_class_id_list = [int(x) for x in object_class_id_list.split(",")]
                objects = self.obj_dict[db_map]
                # Find object_id_list
                object_id_list = list()
                for object_class_id, object_name in zip(object_class_id_list, object_name_list):
                    if (object_class_id, object_name) not in objects:
                        self._parent.msg_error.emit(
                            "Invalid object '{}' for db '{}' at row {}".format(object_name, db_name, i + 1)
                        )
                        return
                    object_id = objects[object_class_id, object_name]
                    object_id_list.append(object_id)
                item = pre_item.copy()
                item.update({'id': id_, 'object_id_list': object_id_list, 'name': name})
                relationship_d.setdefault(db_map, []).append(item)
        if not relationship_d:
            self._parent.msg_error.emit("Nothing to update")
            return
        self._parent.update_relationships(relationship_d)
        super().accept()


class RemoveTreeItemsDialog(EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for removing tree items.

    Attributes:
        parent (TreeViewForm): data store widget
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.setWindowTitle("Remove items")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(RemoveTreeItemsDelegate(self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['type', 'name', 'databases'])
        model_data = list()
        for item_type, db_map_dicts in kwargs.items():
            for db_map_dict in db_map_dicts:
                db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in db_map_dict])
                item = list(db_map_dict.values())[0]
                name = item.get('name')
                if not name:
                    continue
                row_data = [item_type, name, db_names]
                model_data.append(row_data)
                self.db_map_dicts.append(db_map_dict)
        self.model.reset_model(model_data)

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to remove items."""
        item_d = dict()
        for i in range(self.model.rowCount()):
            item_type, _, db_names = self.model.row_data(i)
            db_name_list = db_names.split(",")
            try:
                db_maps = [self._parent.db_name_to_map[x] for x in db_name_list]
            except KeyError as e:
                self._parent.msg_error.emit("Invalid database {0} at row {1}".format(e, i + 1))
                return
            for db_map in db_maps:
                item = self.db_map_dicts[i][db_map]
                item_d.setdefault(db_map, {}).setdefault(item_type, []).append(item)
        if not item_d:
            self._parent.msg_error.emit("Nothing to remove")
            return
        self._parent.remove_tree_items(item_d)
        super().accept()


class ManageParameterTagsDialog(ManageItemsDialog):
    """A dialog to query user's preferences for managing parameter tags.

    Attributes:
        parent (TreeViewForm): data store widget
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Manage parameter tags")
        self.model = HybridTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageParameterTagsDelegate(self))
        self.connect_signals()
        self.orig_data = list()
        model_data = list()
        tag_dict = {}
        for db_map in self._parent.db_maps:
            for parameter_tag in db_map.parameter_tag_list():
                tag_dict.setdefault(parameter_tag.tag, {})[db_map] = parameter_tag
        self.db_map_dicts = list(tag_dict.values())
        for db_map_dict in self.db_map_dicts:
            parameter_tag = list(db_map_dict.values())[0]
            tag = parameter_tag.tag
            description = parameter_tag.description
            remove = None
            db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in db_map_dict])
            row_data = [tag, description]
            self.orig_data.append(row_data.copy())
            row_data.extend([db_names, remove])
            model_data.append(row_data)
        self.model.set_horizontal_header_labels(['parameter tag', 'description', 'databases', 'remove'])
        db_names = ",".join([self._parent.db_map_to_name[db_map] for db_map in self._parent.db_maps])
        self.model.new_item_model.set_default_row(**{'databases': db_names})
        self.model.reset_model(model_data)
        self.create_check_boxes(0, self.model.rowCount() - 1)

    def create_check_boxes(self, start, stop):
        """Create check boxes in remove column."""
        column = self.model.header.index('remove')
        for row in range(start, stop):
            index = self.model.index(row, column)
            check_box = QCheckBox(self)
            self.table_view.setIndexWidget(index, check_box)

    def all_databases(self, row):
        """Returns a list of db names available for a given row.
        Used by delegates.
        """
        if row < self.model.existing_item_model.rowCount():
            return [self._parent.db_map_to_name[db_map] for db_map in self.db_map_dicts[row]]
        return [self._parent.db_map_to_name[db_map] for db_map in self._parent.db_maps]

    @busy_effect
    def accept(self):
        """Collect info from dialog and try to update, remove, add items."""
        # Update and remove
        items_to_update = {}
        items_to_remove = {}
        for i in range(self.model.existing_item_model.rowCount()):
            tag, description, db_names, _ = self.model.existing_item_model.row_data(i)
            db_name_list = db_names.split(",")
            try:
                db_maps = [self._parent.db_name_to_map[x] for x in db_name_list]
            except KeyError as e:
                self._parent.msg_error.emit("Invalid database {0} at row {1}".format(e, i + 1))
                return
            # Remove
            check_box = self.table_view.indexWidget(self.model.index(i, self.model.header.index('remove')))
            if check_box.isChecked():
                for db_map in db_maps:
                    parameter_tag = self.db_map_dicts[i][db_map]
                    items_to_remove.setdefault(db_map, []).append(parameter_tag.id)
                continue
            if not tag:
                self._parent.msg_error.emit("Tag missing at row {}".format(i + 1))
                return
            # Update
            if [tag, description] != self.orig_data[i]:
                for db_map, parameter_tag in db_maps:
                    parameter_tag = self.db_map_dicts[i][db_map]
                    item = {'id': parameter_tag.id, 'tag': tag, 'description': description}
                    items_to_update.setdefault(db_map, []).append(item)
        # Insert
        items_to_add = {}
        offset = self.model.existing_item_model.rowCount()
        for i in range(self.model.new_item_model.rowCount() - 1):  # last row will always be empty
            tag, description, db_names = self.model.new_item_model.row_data(i)
            db_name_list = db_names.split(",")
            try:
                db_maps = [self._parent.db_name_to_map[x] for x in db_name_list]
            except KeyError as e:
                self._parent.msg_error.emit("Invalid database {0} at row {1}".format(e, offset + i + 1))
                return
            if not tag:
                self._parent.msg_error.emit("Tag missing at row {0}".format(offset + i + 1))
                return
            for db_map in db_maps:
                item = {'tag': tag, 'description': description}
                items_to_add.setdefault(db_map, []).append(item)
        if items_to_remove:
            self._parent.remove_parameter_tags(items_to_remove)
        if items_to_update:
            self._parent.update_parameter_tags(items_to_update)
        if items_to_add:
            self._parent.add_parameter_tags(items_to_add)
        super().accept()


class CommitDialog(QDialog):
    """A dialog to query user's preferences for new commit.

    Attributes:
        parent (TreeViewForm): data store widget
        db_names (Iterable): database names
    """

    def __init__(self, parent, *db_names):
        """Initialize class"""
        super().__init__(parent)
        self.commit_msg = None
        self.setWindowTitle('Commit changes to {}'.format(", ".join(db_names)))
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
