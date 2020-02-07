######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes for custom QDialogs to add items to databases.

:author: M. Marin (KTH)
:date:   13.5.2018
"""

from PySide2.QtWidgets import QHBoxLayout, QWidget, QLabel, QComboBox, QSpinBox, QToolButton
from PySide2.QtCore import Slot, Qt
from PySide2.QtGui import QIcon
from ..mvcmodels.empty_row_model import EmptyRowModel
from .custom_delegates import (
    ManageObjectClassesDelegate,
    ManageObjectsDelegate,
    ManageRelationshipClassesDelegate,
    ManageRelationshipsDelegate,
)
from .manage_db_items_dialog import ShowIconColorEditorMixin, GetObjectClassesMixin, GetObjectsMixin, ManageItemsDialog
from ..helpers import default_icon_id


class AddItemsDialog(ManageItemsDialog):
    """A dialog to query user's preferences for new db items."""

    def __init__(self, parent, db_mngr, *db_maps):
        """Init class.

        Args
            parent (DataStoreForm)
            db_mngr (SpineDBManager)
            db_maps (iter) DiffDatabaseMapping instances
        """
        super().__init__(parent, db_mngr)
        self.db_maps = db_maps
        self.keyed_db_maps = {x.codename: x for x in db_maps}
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
        return [x.codename for x in self.db_maps]


class AddObjectClassesDialog(ShowIconColorEditorMixin, AddItemsDialog):
    """A dialog to query user's preferences for new object classes."""

    def __init__(self, parent, db_mngr, *db_maps):
        """Init class.

        Args
            parent (DataStoreForm)
            db_mngr (SpineDBManager)
            db_maps (iter) DiffDatabaseMapping instances
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.setWindowTitle("Add object classes")
        self.model = EmptyRowModel(self)
        self.table_view.setModel(self.model)
        self.combo_box = QComboBox(self)
        self.layout().insertWidget(0, self.combo_box)
        self.db_map_obj_cls_lookup = {
            db_map: {x["name"]: x for x in self.db_mngr.get_object_classes(db_map)} for db_map in self.db_maps
        }
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.table_view.setItemDelegate(ManageObjectClassesDelegate(self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['object class name', 'description', 'display icon', 'databases'])
        databases = ",".join(list(self.keyed_db_maps.keys()))
        self.default_display_icon = default_icon_id()
        self.model.set_default_row(**{'databases': databases, 'display icon': self.default_display_icon})
        self.model.clear()
        insert_at_position_list = ['Insert new classes at the top']
        object_class_names = {x: None for db_map in self.db_maps for x in self.db_map_obj_cls_lookup[db_map]}
        self.object_class_names = list(object_class_names)
        insert_at_position_list.extend(
            ["Insert new classes after '{}'".format(name) for name in self.object_class_names]
        )
        self.combo_box.addItems(insert_at_position_list)

    def connect_signals(self):
        super().connect_signals()
        # pylint: disable=unnecessary-lambda
        self.table_view.itemDelegate().icon_color_editor_requested.connect(
            lambda index: self.show_icon_color_editor(index)
        )

    @Slot(name="accept")
    def accept(self):
        """Collect info from dialog and try to add items."""
        db_map_data = dict()
        # Display order
        combo_index = self.combo_box.currentIndex()
        after_obj_cls = self.object_class_names[combo_index - 1] if combo_index > 0 else None
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            name, description, display_icon, db_names = row_data
            db_name_list = db_names.split(",")
            try:
                db_maps = [self.keyed_db_maps[x] for x in db_name_list]
            except KeyError as e:
                self.parent().msg_error.emit("Invalid database {0} at row {1}".format(e, i + 1))
                return
            if not name:
                self.parent().msg_error.emit("Object class name missing at row {0}".format(i + 1))
                return
            if not display_icon:
                display_icon = self.default_display_icon
            pre_item = {'name': name, 'description': description, 'display_icon': display_icon}
            for db_map in db_maps:
                object_classes = self.db_map_obj_cls_lookup[db_map]
                if not object_classes:
                    # This happens when there's no object classes in the db
                    display_order = 0
                elif after_obj_cls is None:
                    # At the top
                    display_order = list(object_classes.values())[0]["display_order"] - 1
                else:
                    display_order = object_classes[after_obj_cls]["display_order"]
                item = pre_item.copy()
                item['display_order'] = display_order
                db_map_data.setdefault(db_map, []).append(item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to add")
            return
        self.db_mngr.add_object_classes(db_map_data)
        super().accept()


class AddObjectsDialog(GetObjectClassesMixin, AddItemsDialog):
    """A dialog to query user's preferences for new objects.
    """

    def __init__(self, parent, db_mngr, *db_maps, class_name=None, force_default=False):
        """Init class.

        Args
            parent (DataStoreForm)
            db_mngr (SpineDBManager)
            db_maps (iter) DiffDatabaseMapping instances
            class_name (str): default object class name
            force_default (bool): if True, defaults are non-editable
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.setWindowTitle("Add objects")
        self.model = EmptyRowModel(self)
        self.model.force_default = force_default
        self.table_view.setModel(self.model)
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.table_view.setItemDelegate(ManageObjectsDelegate(self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['object class name', 'object name', 'description', 'databases'])
        self.db_map_obj_cls_lookup = self.make_db_map_obj_cls_lookup()
        if class_name:
            default_db_maps = [db_map for db_map, names in self.db_map_obj_cls_lookup.items() if class_name in names]
            db_names = ",".join(
                [db_name for db_name, db_map in self.keyed_db_maps.items() if db_map in default_db_maps]
            )
        else:
            db_names = ",".join(list(self.keyed_db_maps.keys()))
        self.model.set_default_row(**{'object class name': class_name, 'databases': db_names})
        self.model.clear()

    @Slot(name="accept")
    def accept(self):
        """Collect info from dialog and try to add items."""
        db_map_data = dict()
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            class_name, name, description, db_names = row_data
            if not name:
                self.parent().msg_error.emit("Object name missing at row {}".format(i + 1))
                return
            pre_item = {'name': name, 'description': description}
            for db_name in db_names.split(","):
                if db_name not in self.keyed_db_maps:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(db_name, i + 1))
                    return
                db_map = self.keyed_db_maps[db_name]
                object_classes = self.db_map_obj_cls_lookup[db_map]
                if class_name not in object_classes:
                    self.parent().msg_error.emit(
                        "Invalid object class '{}' for db '{}' at row {}".format(class_name, db_name, i + 1)
                    )
                    return
                class_id = object_classes[class_name]["id"]
                item = pre_item.copy()
                item['class_id'] = class_id
                db_map_data.setdefault(db_map, []).append(item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to add")
            return
        self.db_mngr.add_objects(db_map_data)
        super().accept()


class AddRelationshipClassesDialog(GetObjectClassesMixin, AddItemsDialog):
    """A dialog to query user's preferences for new relationship classes."""

    def __init__(self, parent, db_mngr, *db_maps, object_class_one_name=None, force_default=False):
        """Init class.

        Args
            parent (DataStoreForm)
            db_mngr (SpineDBManager)
            db_maps (iter) DiffDatabaseMapping instances
            object_class_one_name (str): default object class name
            force_default (bool): if True, defaults are non-editable
        """
        super().__init__(parent, db_mngr, *db_maps)
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
        self.db_map_obj_cls_lookup = self.make_db_map_obj_cls_lookup()
        if object_class_one_name:
            default_db_maps = [
                db_map for db_map, names in self.db_map_obj_cls_lookup.items() if object_class_one_name in names
            ]
            db_names = ",".join(
                [db_name for db_name, db_map in self.keyed_db_maps.items() if db_map in default_db_maps]
            )
        else:
            db_names = ",".join(list(self.keyed_db_maps.keys()))
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
            else:
                col_data = lambda j: self.model.index(row, j).data()  # pylint: disable=cell-var-from-loop
                obj_cls_names = [col_data(j) for j in range(self.number_of_dimensions) if col_data(j)]
                if len(obj_cls_names) == 1:
                    relationship_class_name = obj_cls_names[0] + "__"
                else:
                    relationship_class_name = "__".join(obj_cls_names)
                self.model.setData(self.model.index(row, self.number_of_dimensions), relationship_class_name)

    @Slot(name="accept")
    def accept(self):
        """Collect info from dialog and try to add items."""
        db_map_data = dict()
        name_column = self.model.horizontal_header_labels().index("relationship class name")
        db_column = self.model.horizontal_header_labels().index("databases")
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            relationship_class_name = row_data[name_column]
            if not relationship_class_name:
                self.parent().msg_error.emit("Relationship class name missing at row {}".format(i + 1))
                return
            pre_item = {'name': relationship_class_name}
            db_names = row_data[db_column]
            for db_name in db_names.split(","):
                if db_name not in self.keyed_db_maps:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(db_name, i + 1))
                    return
                db_map = self.keyed_db_maps[db_name]
                object_classes = self.db_map_obj_cls_lookup[db_map]
                object_class_id_list = list()
                for column in range(name_column):  # Leave 'name' column outside
                    object_class_name = row_data[column]
                    if object_class_name not in object_classes:
                        self.parent().msg_error.emit(
                            "Invalid object class '{}' for db '{}' at row {}".format(object_class_name, db_name, i + 1)
                        )
                        return
                    object_class_id = object_classes[object_class_name]["id"]
                    object_class_id_list.append(object_class_id)
                item = pre_item.copy()
                item['object_class_id_list'] = object_class_id_list
                db_map_data.setdefault(db_map, []).append(item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to add")
            return
        self.db_mngr.add_relationship_classes(db_map_data)
        super().accept()


class AddRelationshipsDialog(GetObjectsMixin, AddItemsDialog):
    """A dialog to query user's preferences for new relationships."""

    def __init__(
        self,
        parent,
        db_mngr,
        *db_maps,
        relationship_class_key=None,
        object_class_name=None,
        object_name=None,
        force_default=False,
    ):
        """Init class.

        Args
            parent (DataStoreForm)
            db_mngr (SpineDBManager)
            db_maps (iter) DiffDatabaseMapping instances
            relationship_class_key (tuple): (class_name, object_class_name_list)
            object_name (str): default object name
            object_class_name (str): default object class name
            force_default (bool): if True, defaults are non-editable
        """
        super().__init__(parent, db_mngr, *db_maps)
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
        self.db_map_obj_lookup = self.make_db_map_obj_lookup()
        self.db_map_rel_cls_lookup = self.make_db_map_rel_cls_lookup()
        relationship_class_keys = {
            x: None for rel_cls_list in self.db_map_rel_cls_lookup.values() for x in rel_cls_list
        }
        self.relationship_class_keys = list(relationship_class_keys)
        self.combo_box.addItems(["{0} ({1})".format(*key) for key in self.relationship_class_keys])
        self.table_view.setItemDelegate(ManageRelationshipsDelegate(self))
        self.connect_signals()
        if relationship_class_key in self.relationship_class_keys:
            current_index = self.relationship_class_keys.index(relationship_class_key)
            self.combo_box.setCurrentIndex(current_index)
            self.class_name, self.object_class_name_list = relationship_class_key
            self.reset_model()
        else:
            self.combo_box.setCurrentIndex(-1)
        self.combo_box.setEnabled(not force_default)

    def connect_signals(self):
        """Connect signals to slots."""
        self.combo_box.currentIndexChanged.connect(self.call_reset_model)
        super().connect_signals()

    @Slot("int", name='call_reset_model')
    def call_reset_model(self, index):
        """Called when relationship class's combobox's index changes.
        Update relationship_class attribute accordingly and reset model."""
        try:
            self.class_name, self.object_class_name_list = self.relationship_class_keys[index]
        except IndexError:
            return
        self.reset_model()

    def reset_model(self):
        """Setup model according to current relationship class selected in combobox.
        """
        default_db_maps = [
            db_map
            for db_map, rel_cls_list in self.db_map_rel_cls_lookup.items()
            if (self.class_name, self.object_class_name_list) in rel_cls_list
        ]
        object_class_name_list = self.object_class_name_list.split(",")
        db_names = ",".join([db_name for db_name, db_map in self.keyed_db_maps.items() if db_map in default_db_maps])
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

    @Slot(name="accept")
    def accept(self):
        """Collect info from dialog and try to add items."""
        db_map_data = dict()
        name_column = self.model.horizontal_header_labels().index("relationship name")
        db_column = self.model.horizontal_header_labels().index("databases")
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            object_name_list = [row_data[column] for column in range(name_column)]
            relationship_name = row_data[name_column]
            if not relationship_name:
                self.parent().msg_error.emit("Relationship name missing at row {}".format(i + 1))
                return
            pre_item = {'name': relationship_name}
            db_names = row_data[db_column]
            for db_name in db_names.split(","):
                if db_name not in self.keyed_db_maps:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(db_name, i + 1))
                    return
                db_map = self.keyed_db_maps[db_name]
                relationship_classes = self.db_map_rel_cls_lookup[db_map]
                if (self.class_name, self.object_class_name_list) not in relationship_classes:
                    self.parent().msg_error.emit(
                        "Invalid relationship class '{}' for db '{}' at row {}".format(self.class_name, db_name, i + 1)
                    )
                    return
                rel_cls = relationship_classes[self.class_name, self.object_class_name_list]
                class_id = rel_cls["id"]
                object_class_id_list = rel_cls["object_class_id_list"]
                object_class_id_list = [int(x) for x in object_class_id_list.split(",")]
                objects = self.db_map_obj_lookup[db_map]
                object_id_list = list()
                for object_class_id, object_name in zip(object_class_id_list, object_name_list):
                    if (object_class_id, object_name) not in objects:
                        self.parent().msg_error.emit(
                            "Invalid object '{}' for db '{}' at row {}".format(object_name, db_name, i + 1)
                        )
                        return
                    object_id = objects[object_class_id, object_name]["id"]
                    object_id_list.append(object_id)
                item = pre_item.copy()
                item.update({'object_id_list': object_id_list, 'class_id': class_id})
                db_map_data.setdefault(db_map, []).append(item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to add")
            return
        self.db_mngr.add_relationships(db_map_data)
        super().accept()
