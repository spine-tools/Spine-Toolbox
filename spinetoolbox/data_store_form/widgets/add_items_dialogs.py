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

from itertools import product
from PySide2.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QWidget,
    QLabel,
    QLineEdit,
    QDialog,
    QComboBox,
    QSpinBox,
    QToolButton,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QDialogButtonBox,
)
from PySide2.QtCore import Slot, Qt, QSize
from PySide2.QtGui import QIcon
from ...mvcmodels.empty_row_model import EmptyRowModel
from ...mvcmodels.compound_table_model import CompoundTableModel
from ...mvcmodels.minimal_table_model import MinimalTableModel
from .custom_delegates import (
    ManageObjectClassesDelegate,
    ManageObjectsDelegate,
    ManageRelationshipClassesDelegate,
    ManageRelationshipsDelegate,
)
from .manage_items_dialogs import (
    ShowIconColorEditorMixin,
    GetObjectClassesMixin,
    GetObjectsMixin,
    GetRelationshipClassesMixin,
    ManageItemsDialog,
    ManageItemsDialogBase,
)
from ...helpers import default_icon_id


class AddReadyRelationshipsDialog(ManageItemsDialogBase):
    """A dialog to let the user add new 'ready' relationships."""

    def __init__(self, parent, relationships_class, relationships, db_mngr, *db_maps):
        """Init class.

        Args
            relationships_class (dict)
            relationships (list(list(str))
            parent (DataStoreForm)
            db_mngr (SpineDBManager)
            db_maps (iter) DiffDatabaseMapping instances
        """
        super().__init__(parent, db_mngr)
        self.relationship_class = relationships_class
        self.relationships = relationships
        self.db_maps = db_maps
        label = QLabel("<p>Please check the relationships you want to add and press <b>Ok</b>.</p>")
        label.setWordWrap(True)
        self.layout().addWidget(label, 0, 0)
        self.layout().addWidget(self.table_view, 1, 0)
        self.layout().addWidget(self.button_box, 2, 0, -1, -1)
        self.setWindowTitle("Add '{0}' relationships".format(self.relationship_class["name"]))
        self.populate_table_view()
        self.connect_signals()

    def make_table_view(self):
        return QTableWidget(self)

    def populate_table_view(self):
        object_class_name_list = self.relationship_class["object_class_name_list"].split(",")
        self.table_view.setRowCount(len(self.relationships))
        self.table_view.setColumnCount(len(object_class_name_list) + 1)
        labels = [""] + object_class_name_list
        self.table_view.setHorizontalHeaderLabels(labels)
        self.table_view.verticalHeader().hide()
        for row, relationship in enumerate(self.relationships):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsEnabled)
            item.setCheckState(Qt.Checked)
            self.table_view.setItem(row, 0, item)
            for column, object_name in enumerate(relationship):
                item = QTableWidgetItem(object_name)
                item.setFlags(Qt.ItemIsEnabled)
                self.table_view.setItem(row, column + 1, item)
        self.table_view.resizeColumnsToContents()
        self.resize_window_to_columns()

    def connect_signals(self):
        super().connect_signals()
        self.table_view.cellClicked.connect(self._handle_table_view_cell_clicked)
        self.table_view.selectionModel().currentChanged.connect(self._handle_table_view_current_changed)

    def _handle_table_view_cell_clicked(self, row, column):
        item = self.table_view.item(row, 0)
        check_state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
        item.setCheckState(check_state)

    def _handle_table_view_current_changed(self, current, _previous):
        if current.isValid():
            self.table_view.selectionModel().clearCurrentIndex()

    def accept(self):
        super().accept()
        data = []
        for row in range(self.table_view.rowCount()):
            if self.table_view.item(row, 0).checkState() != Qt.Checked:
                continue
            relationship = self.relationships[row]
            data.append([self.relationship_class["name"], relationship])
        db_map_data = {db_map: {"relationships": data} for db_map in self.db_maps}
        self.db_mngr.import_data(db_map_data, command_text="Add relationships")


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
        self.layout().addWidget(self.remove_rows_button, 1, 0)
        self.layout().addWidget(self.button_box, 2, 0, -1, -1)

    def connect_signals(self):
        super().connect_signals()
        self.remove_rows_button.clicked.connect(self.remove_selected_rows)

    @Slot(bool)
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
        self.layout().addWidget(self.table_view, 0, 0)
        self.layout().addWidget(self.remove_rows_button, 1, 0)
        self.layout().addWidget(self.button_box, 2, 0, -1, -1)
        self.display_order = {
            db_map: max((x["display_order"] for x in self.db_mngr.get_items(db_map, "object class")), default=-1)
            for db_map in self.db_maps
        }
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.table_view.setItemDelegate(ManageObjectClassesDelegate(self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['object class name', 'description', 'display icon', 'databases'])
        databases = ",".join(list(self.keyed_db_maps.keys()))
        self.default_display_icon = default_icon_id()
        self.model.set_default_row(**{'databases': databases, 'display icon': self.default_display_icon})
        self.model.clear()

    def connect_signals(self):
        super().connect_signals()
        # pylint: disable=unnecessary-lambda
        self.table_view.itemDelegate().icon_color_editor_requested.connect(
            lambda index: self.show_icon_color_editor(index)
        )

    def all_db_maps(self, row):
        """Returns a list of db maps available for a given row.
        Used by ShowIconColorEditorMixin.
        """
        return self.db_maps

    @Slot()
    def accept(self):
        """Collect info from dialog and try to add items."""
        db_map_data = dict()
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            name, description, display_icon, db_names = row_data
            if db_names is None:
                db_names = ""
            db_name_list = db_names.split(",")
            try:
                db_maps = [self.keyed_db_maps[x] for x in db_name_list]
            except KeyError as e:
                self.parent().msg_error.emit("Invalid database {0} at row {1}".format(e, i + 1))
                return
            if not name:
                self.parent().msg_error.emit("Object class missing at row {0}".format(i + 1))
                return
            if not display_icon:
                display_icon = self.default_display_icon
            pre_item = {'name': name, 'description': description, 'display_icon': display_icon}
            for db_map in db_maps:
                item = pre_item.copy()
                self.display_order[db_map] += 1
                item['display_order'] = self.display_order[db_map]
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

    @Slot()
    def accept(self):
        """Collect info from dialog and try to add items."""
        db_map_data = dict()
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            class_name, name, description, db_names = row_data
            if db_names is None:
                db_names = ""
            if not name:
                self.parent().msg_error.emit("Object missing at row {}".format(i + 1))
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
        self.dimension_count_widget = QWidget(self)
        layout = QHBoxLayout(self.dimension_count_widget)
        layout.addWidget(QLabel("Number of dimensions"))
        self.spin_box = QSpinBox(self)
        self.spin_box.setMinimum(1)
        layout.addWidget(self.spin_box)
        layout.addStretch()
        self.layout().addWidget(self.dimension_count_widget, 0, 0, 1, -1)
        self.layout().addWidget(self.table_view, 1, 0)
        self.layout().addWidget(self.remove_rows_button, 2, 0)
        self.layout().addWidget(self.button_box, 3, 0, -1, -1)
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cubes_minus.svg"))
        self.table_view.setItemDelegate(ManageRelationshipClassesDelegate(self))
        self.number_of_dimensions = 1
        self.connect_signals()
        self.model.set_horizontal_header_labels(
            ['object class name (1)', 'relationship class name', 'description', 'databases']
        )
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
        self.model.set_default_row(**{'object class name (1)': object_class_one_name, 'databases': db_names})
        self.model.clear()

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        self.spin_box.valueChanged.connect(self._handle_spin_box_value_changed)

    @Slot(int)
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
        column_name = "object class name ({0})".format(self.number_of_dimensions)
        self.model.insertColumns(column, 1)
        self.model.insert_horizontal_header_labels(column, [column_name])
        self.table_view.resizeColumnToContents(column)

    def remove_column(self):
        self.number_of_dimensions -= 1
        column = self.number_of_dimensions
        self.model.header.pop(column)
        self.model.removeColumns(column, 1)

    @Slot("QModelIndex", "QModelIndex", "QVector")
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

    @Slot()
    def accept(self):
        """Collect info from dialog and try to add items."""
        db_map_data = dict()
        name_column = self.model.horizontal_header_labels().index("relationship class name")
        description_column = self.model.horizontal_header_labels().index("description")
        db_column = self.model.horizontal_header_labels().index("databases")
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            relationship_class_name = row_data[name_column]
            if not relationship_class_name:
                self.parent().msg_error.emit("Relationship class missing at row {}".format(i + 1))
                return
            description = row_data[description_column]
            pre_item = {'name': relationship_class_name, 'description': description}
            db_names = row_data[db_column]
            if db_names is None:
                db_names = ""
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


class AddOrManageRelationshipsDialog(GetRelationshipClassesMixin, GetObjectsMixin, AddItemsDialog):
    """A dialog to query user's preferences for new relationships."""

    def __init__(self, parent, db_mngr, *db_maps):
        """Init class.

        Args
            parent (DataStoreForm)
            db_mngr (SpineDBManager)
            db_maps (iter) DiffDatabaseMapping instances
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.model = self.make_model()
        self.table_view.setModel(self.model)
        self.header_widget = QWidget(self)
        layout = QHBoxLayout(self.header_widget)
        layout.addWidget(QLabel("Relationship class"))
        self.rel_cls_combo_box = QComboBox(self)
        layout.addWidget(self.rel_cls_combo_box)
        layout.addStretch()
        self.layout().addWidget(self.header_widget, 0, 0, 1, -1)
        self.layout().addWidget(self.table_view, 1, 0)
        self.layout().addWidget(self.remove_rows_button, 2, 0)
        self.layout().addWidget(self.button_box, 3, 0, -1, -1)
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cubes_minus.svg"))
        self.db_map_obj_lookup = self.make_db_map_obj_lookup()
        self.db_map_rel_cls_lookup = self.make_db_map_rel_cls_lookup()
        self.relationship_class_keys = []
        self.class_name = None
        self.object_class_name_list = None

    def make_model(self):
        raise NotImplementedError()

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        self.rel_cls_combo_box.currentIndexChanged.connect(self.reset_model)

    @Slot(int)
    def reset_model(self, index):
        """Called when relationship class's combobox's index changes.
        Update relationship_class attribute accordingly and reset model."""
        raise NotImplementedError()


class AddRelationshipsDialog(AddOrManageRelationshipsDialog):
    """A dialog to query user's preferences for new relationships."""

    def __init__(
        self, parent, db_mngr, *db_maps, relationship_class_key=(), object_names_by_class_name=None, force_default=False
    ):
        """Init class.

        Args
            parent (DataStoreForm)
            db_mngr (SpineDBManager)
            db_maps (iter) DiffDatabaseMapping instances
            relationship_class_key (tuple(str,str)): relationships class name, object class name list string
            object_names_by_class_name (dict): mapping object class names to default object names
            force_default (bool): if True, defaults are non-editable
        """
        super().__init__(parent, db_mngr, *db_maps)
        if object_names_by_class_name is None:
            object_names_by_class_name = {}
        self.object_names_by_class_name = object_names_by_class_name
        self.relationship_class = None
        self.model.force_default = force_default
        self.setWindowTitle("Add relationships")
        self.table_view.setItemDelegate(ManageRelationshipsDelegate(self))
        self.rel_cls_combo_box.setEnabled(not force_default)
        self.relationship_class_keys = [
            key for relationship_classes in self.db_map_rel_cls_lookup.values() for key in relationship_classes
        ]
        self.rel_cls_combo_box.addItems(["{0} ({1})".format(*key) for key in self.relationship_class_keys])
        try:
            current_index = self.relationship_class_keys.index(relationship_class_key)
            self.reset_model(current_index)
            self._handle_model_reset()
        except ValueError:
            current_index = -1
        self.rel_cls_combo_box.setCurrentIndex(current_index)
        self.connect_signals()

    def make_model(self):
        return EmptyRowModel(self)

    @Slot(int)
    def reset_model(self, index):
        """Setup model according to current relationship class selected in combobox.
        """
        self.class_name, self.object_class_name_list = self.relationship_class_keys[index]
        default_db_maps = [
            db_map
            for db_map, rel_cls_list in self.db_map_rel_cls_lookup.items()
            if (self.class_name, self.object_class_name_list) in rel_cls_list
        ]
        object_class_name_list = self.object_class_name_list.split(",")
        db_names = ",".join([db_name for db_name, db_map in self.keyed_db_maps.items() if db_map in default_db_maps])
        header = object_class_name_list + ['relationship name', 'databases']
        self.model.set_horizontal_header_labels(header)
        defaults = {'databases': db_names}
        if self.object_names_by_class_name:
            defaults.update({key: value for key, value in self.object_names_by_class_name.items()})
        self.model.set_default_row(**defaults)
        self.model.clear()

    @Slot("QModelIndex", "QModelIndex", "QVector")
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
                relationship_name = self.class_name + "_"
                if len(obj_names) == 1:
                    relationship_name += obj_names[0] + "__"
                else:
                    relationship_name += "__".join(obj_names)
                self.model.setData(self.model.index(row, number_of_dimensions), relationship_name)

    @Slot()
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
                self.parent().msg_error.emit("Relationship missing at row {}".format(i + 1))
                return
            pre_item = {'name': relationship_name}
            db_names = row_data[db_column]
            if db_names is None:
                db_names = ""
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


class ManageRelationshipsDialog(AddOrManageRelationshipsDialog):
    """A dialog to query user's preferences for managing relationships.
    """

    def __init__(self, parent, db_mngr, *db_maps, relationship_class_key=None):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            db_mngr (SpineDBManager): the manager to do the removal
            db_maps (iter): DiffDatabaseMapping instances
            relationship_class_key (str, optional): relationships class name, object class name list string.
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.setWindowTitle("Manage relationships")
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.remove_rows_button.setToolTip("<p>Remove selected relationships.</p>")
        self.remove_rows_button.setIconSize(QSize(24, 24))
        self.db_map = db_maps[0]
        self.relationships = dict()
        layout = self.header_widget.layout()
        self.db_combo_box = QComboBox(self)
        layout.addSpacing(32)
        layout.addWidget(QLabel("Database"))
        layout.addWidget(self.db_combo_box)
        self.splitter = QSplitter(self)
        self.add_button = QToolButton(self)
        self.add_button.setToolTip("<p>Add relationships by combining selected available objects.</p>")
        self.add_button.setIcon(QIcon(":/icons/menu_icons/cubes_plus.svg"))
        self.add_button.setIconSize(QSize(24, 24))
        self.add_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.add_button.setText(">>")
        label_available = QLabel("Available objects")
        label_existing = QLabel("Existing relationships")
        self.layout().addWidget(self.header_widget, 0, 0, 1, 4, Qt.AlignHCenter)
        self.layout().addWidget(label_available, 1, 0)
        self.layout().addWidget(label_existing, 1, 2)
        self.layout().addWidget(self.splitter, 2, 0)
        self.layout().addWidget(self.add_button, 2, 1)
        self.layout().addWidget(self.table_view, 2, 2)
        self.layout().addWidget(self.remove_rows_button, 2, 3)
        self.layout().addWidget(self.button_box, 3, 0, -1, -1)
        self.hidable_widgets = [
            self.add_button,
            label_available,
            label_existing,
            self.table_view,
            self.remove_rows_button,
        ]
        for widget in self.hidable_widgets:
            widget.hide()
        self.existing_items_model = MinimalTableModel(self, lazy=False)
        self.new_items_model = MinimalTableModel(self, lazy=False)
        self.model.sub_models = [self.new_items_model, self.existing_items_model]
        self.db_combo_box.addItems([db_map.codename for db_map in db_maps])
        self.reset_relationship_class_combo_box(db_maps[0].codename, relationship_class_key)
        self.connect_signals()

    def make_model(self):
        return CompoundTableModel(self)

    def splitter_widgets(self):
        return [self.splitter.widget(i) for i in range(self.splitter.count())]

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        self.db_combo_box.currentTextChanged.connect(self.reset_relationship_class_combo_box)
        self.add_button.clicked.connect(self.add_relationships)

    @Slot(str)
    def reset_relationship_class_combo_box(self, database, relationship_class_key=None):
        self.db_map = self.keyed_db_maps[database]
        self.relationship_class_keys = list(self.db_map_rel_cls_lookup[self.db_map])
        self.rel_cls_combo_box.addItems([f"{name}" for name, _ in self.relationship_class_keys])
        try:
            current_index = self.relationship_class_keys.index(relationship_class_key)
            self.reset_model(current_index)
            self._handle_model_reset()
        except ValueError:
            current_index = -1
        self.rel_cls_combo_box.setCurrentIndex(current_index)

    @Slot(bool)
    def add_relationships(self, checked=True):
        object_names = [[item.text(0) for item in wg.selectedItems()] for wg in self.splitter_widgets()]
        candidate = list(product(*object_names))
        existing = self.new_items_model._main_data + self.existing_items_model._main_data
        to_add = list(set(candidate) - set(existing))
        count = len(to_add)
        self.new_items_model.insertRows(0, count)
        self.new_items_model._main_data[0:count] = to_add
        self.model.refresh()

    @Slot(int)
    def reset_model(self, index):
        """Setup model according to current relationship class selected in combobox.
        """
        self.class_name, self.object_class_name_list = self.relationship_class_keys[index]
        object_class_name_list = self.object_class_name_list.split(",")
        self.model.set_horizontal_header_labels(object_class_name_list)
        self.existing_items_model.set_horizontal_header_labels(object_class_name_list)
        self.new_items_model.set_horizontal_header_labels(object_class_name_list)
        self.relationships.clear()
        for db_map in self.db_maps:
            relationship_classes = self.db_map_rel_cls_lookup[db_map]
            rel_cls = relationship_classes.get((self.class_name, self.object_class_name_list), None)
            if rel_cls is None:
                continue
            for relationship in self.db_mngr.get_items_by_field(db_map, "relationship", "class_id", rel_cls["id"]):
                key = tuple(relationship["object_name_list"].split(","))
                self.relationships[key] = relationship
        existing_items = list(self.relationships)
        self.existing_items_model.reset_model(existing_items)
        self.model.refresh()
        self.model.modelReset.emit()
        for wg in self.splitter_widgets():
            wg.deleteLater()
        for name in object_class_name_list:
            tree_widget = QTreeWidget(self)
            tree_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
            tree_widget.setColumnCount(1)
            tree_widget.setIndentation(0)
            header_item = QTreeWidgetItem([name])
            header_item.setTextAlignment(0, Qt.AlignHCenter)
            tree_widget.setHeaderItem(header_item)
            objects = self.db_mngr.get_items_by_field(self.db_map, "object", "class_name", name)
            items = [QTreeWidgetItem([obj["name"]]) for obj in objects]
            tree_widget.addTopLevelItems(items)
            tree_widget.resizeColumnToContents(0)
            self.splitter.addWidget(tree_widget)
        sizes = [wg.columnWidth(0) for wg in self.splitter_widgets()]
        self.splitter.setSizes(sizes)
        for widget in self.hidable_widgets:
            widget.show()

    def resize_window_to_columns(self, height=None):
        table_view_width = (
            self.table_view.frameWidth() * 2
            + self.table_view.verticalHeader().width()
            + self.table_view.horizontalHeader().length()
        )
        self.table_view.setMinimumWidth(table_view_width)
        self.table_view.setMinimumHeight(self.table_view.verticalHeader().defaultSectionSize() * 16)
        margins = self.layout().contentsMargins()
        if height is None:
            height = self.sizeHint().height()
        self.resize(
            margins.left() + margins.right() + table_view_width + self.add_button.width() + self.splitter.width(),
            height,
        )

    @Slot()
    def accept(self):
        """Collect info from dialog and try to add items."""
        keys_to_remove = set(self.relationships) - set(self.existing_items_model._main_data)
        to_remove = [self.relationships[key] for key in keys_to_remove]
        self.db_mngr.remove_items({self.db_map: {"relationship": to_remove}})
        to_add = [[self.class_name, object_name_list] for object_name_list in self.new_items_model._main_data]
        self.db_mngr.import_data({self.db_map: {"relationships": to_add}}, command_text="Add relationships")
        super().accept()


class AddOrManageObjectGroupDialog(QDialog):
    def __init__(self, parent, object_class_item, db_mngr, *db_maps):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            object_class_item (ObjectClassItem)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping)
        """
        super().__init__(parent)
        self.object_class_item = object_class_item
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self.db_map = db_maps[0]
        self.db_maps_by_codename = {db_map.codename: db_map for db_map in db_maps}
        self.db_combo_box = QComboBox(self)
        self.header_widget = QWidget(self)
        self.group_name_line_edit = QLineEdit(self)
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.addWidget(QLabel(f"Group name: "))
        header_layout.addWidget(self.group_name_line_edit)
        header_layout.addSpacing(32)
        header_layout.addWidget(QLabel("Database"))
        header_layout.addWidget(self.db_combo_box)
        self.non_members_tree = QTreeWidget(self)
        self.non_members_tree.setHeaderLabel("Non members")
        self.non_members_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.non_members_tree.setColumnCount(1)
        self.non_members_tree.setIndentation(0)
        self.members_tree = QTreeWidget(self)
        self.members_tree.setHeaderLabel("Members")
        self.members_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.members_tree.setColumnCount(1)
        self.members_tree.setIndentation(0)
        self.add_button = QToolButton()
        self.add_button.setToolTip("<p>Add selected non-members.</p>")
        self.add_button.setIcon(QIcon(":/icons/menu_icons/cube_plus.svg"))
        self.add_button.setIconSize(QSize(24, 24))
        self.add_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.add_button.setText(">>")
        self.remove_button = QToolButton()
        self.remove_button.setToolTip("<p>Remove selected members.</p>")
        self.remove_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.remove_button.setIconSize(QSize(24, 24))
        self.remove_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.remove_button.setText("<<")
        self.vertical_button_widget = QWidget()
        vertical_button_layout = QVBoxLayout(self.vertical_button_widget)
        vertical_button_layout.addStretch()
        vertical_button_layout.addWidget(self.add_button)
        vertical_button_layout.addWidget(self.remove_button)
        vertical_button_layout.addStretch()
        self.button_box = QDialogButtonBox(self)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        layout = QGridLayout(self)
        layout.addWidget(self.header_widget, 0, 0, 1, 3, Qt.AlignHCenter)
        layout.addWidget(self.non_members_tree, 1, 0)
        layout.addWidget(self.vertical_button_widget, 1, 1)
        layout.addWidget(self.members_tree, 1, 2)
        layout.addWidget(self.button_box, 2, 0, 1, 3)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.db_combo_box.addItems(list(self.db_maps_by_codename))
        self.db_map_object_ids = {
            db_map: {
                x["name"]: x["id"]
                for x in self.db_mngr.get_items_by_field(
                    self.db_map, "object", "class_id", self.object_class_item.db_map_id(db_map)
                )
            }
            for db_map in db_maps
        }
        self.reset_list_widgets(db_maps[0].codename)
        self.connect_signals()

    def connect_signals(self):
        """Connect signals to slots."""
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.db_combo_box.currentTextChanged.connect(self.reset_list_widgets)
        self.add_button.clicked.connect(self.add_members)
        self.remove_button.clicked.connect(self.remove_members)

    def reset_list_widgets(self, database):
        self.db_map = self.db_maps_by_codename[database]
        object_ids = self.db_map_object_ids[self.db_map]
        members = []
        non_members = []
        for obj_name, obj_id in object_ids.items():
            if obj_id in self.initial_member_ids():
                members.append(obj_name)
            elif obj_id != self.initial_entity_id():
                non_members.append(obj_name)
        member_items = [QTreeWidgetItem([obj_name]) for obj_name in members]
        non_member_items = [QTreeWidgetItem([obj_name]) for obj_name in non_members]
        self.members_tree.addTopLevelItems(member_items)
        self.non_members_tree.addTopLevelItems(non_member_items)

    def initial_member_ids(self):
        raise NotImplementedError()

    def initial_entity_id(self):
        raise NotImplementedError()

    @Slot(bool)
    def add_members(self, checked=False):
        indexes = sorted(
            [self.non_members_tree.indexOfTopLevelItem(x) for x in self.non_members_tree.selectedItems()], reverse=True
        )
        items = [self.non_members_tree.takeTopLevelItem(ind) for ind in indexes]
        self.members_tree.addTopLevelItems(items)

    @Slot(bool)
    def remove_members(self, checked=False):
        indexes = sorted(
            [self.members_tree.indexOfTopLevelItem(x) for x in self.members_tree.selectedItems()], reverse=True
        )
        items = [self.members_tree.takeTopLevelItem(ind) for ind in indexes]
        self.non_members_tree.addTopLevelItems(items)

    def _check_validity(self):
        if not self.members_tree.topLevelItemCount():
            self.parent().msg_error.emit("Please select at least one member object.")
            return False
        return True


class AddObjectGroupDialog(AddOrManageObjectGroupDialog):
    def __init__(self, parent, object_class_item, db_mngr, *db_maps):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            object_item (ObjectItem)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping)
        """
        super().__init__(parent, object_class_item, db_mngr, *db_maps)
        self.setWindowTitle("Add object group")
        self.group_name_line_edit.setFocus()
        self.group_name_line_edit.setPlaceholderText("Type group name here")

    def initial_member_ids(self):
        return set()

    def initial_entity_id(self):
        return None

    def _check_validity(self):
        if not super()._check_validity():
            return False
        group_name = self.group_name_line_edit.text()
        if group_name in self.db_map_object_ids[self.db_map]:
            self.parent().msg_error.emit(
                f"An object called {group_name} already exists in this class. Please select a different group name."
            )
            return False
        return True

    @Slot()
    def accept(self):
        if not self._check_validity():
            return
        class_name = self.object_class_item.display_data
        group_name = self.group_name_line_edit.text()
        member_names = {item.text(0) for item in self.members_tree.findItems("*", Qt.MatchWildcard)}
        db_map_data = {
            self.db_map: {
                "objects": [(class_name, group_name)],
                "object_groups": [(self.object_class_item.display_data, group_name, member_names)],
            }
        }
        self.db_mngr.import_data(db_map_data, command_text="Add object group")
        super().accept()


class ManageObjectGroupDialog(AddOrManageObjectGroupDialog):
    def __init__(self, parent, object_item, db_mngr, *db_maps):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            object_item (ObjectItem)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping)
        """
        self.object_item = object_item
        super().__init__(parent, object_item.parent_item, db_mngr, *db_maps)
        self.setWindowTitle("Manage object group")
        self.group_name_line_edit.setReadOnly(True)
        self.group_name_line_edit.setText(object_item.display_data)

    def initial_member_ids(self):
        return self.object_item.db_map_member_ids(self.db_map)

    def initial_entity_id(self):
        return self.object_item.db_map_id(self.db_map)

    @Slot()
    def accept(self):
        if not self._check_validity():
            return
        obj = self.object_item.db_map_data(self.db_map)
        current_member_ids = {
            self.db_map_object_ids[self.db_map][item.text(0)]
            for item in self.members_tree.findItems("*", Qt.MatchWildcard)
        }
        added = current_member_ids - self.initial_member_ids()
        removed = self.initial_member_ids() - current_member_ids
        db_map_data_to_add = {
            self.db_map: [
                {"entity_id": obj["id"], "entity_class_id": obj["class_id"], "member_id": member_id}
                for member_id in added
            ]
        }
        db_map_typed_data_to_remove = {
            self.db_map: {
                "entity group": [
                    x for x in self.object_item.db_map_entity_groups(self.db_map) if x["member_id"] in removed
                ]
            }
        }
        self.db_mngr.add_entity_groups(db_map_data_to_add)
        self.db_mngr.remove_items(db_map_typed_data_to_remove)
        super().accept()
