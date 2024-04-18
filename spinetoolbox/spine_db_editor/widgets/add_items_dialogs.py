######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

""" Classes for custom QDialogs to add items to databases. """
from contextlib import suppress
from itertools import product
from PySide6.QtWidgets import (
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
from PySide6.QtCore import Slot, Qt, QSize, QModelIndex
from PySide6.QtGui import QIcon
from spinedb_api.helpers import name_from_elements, name_from_dimensions
from ..helpers import string_to_bool, string_to_display_icon
from ...mvcmodels.empty_row_model import EmptyRowModel
from ...mvcmodels.compound_table_model import CompoundTableModel
from ...mvcmodels.minimal_table_model import MinimalTableModel
from ...helpers import DB_ITEM_SEPARATOR
from .custom_delegates import ManageEntityClassesDelegate, ManageEntitiesDelegate
from .manage_items_dialogs import (
    ShowIconColorEditorMixin,
    GetEntityClassesMixin,
    GetEntitiesMixin,
    ManageItemsDialog,
    DialogWithTableAndButtons,
)


class AddReadyEntitiesDialog(DialogWithTableAndButtons):
    """A dialog to let the user add new 'ready' multidimensional entities."""

    def __init__(self, parent, entity_class, entities, db_mngr, *db_maps, commit_data=True):
        """
        Args:
            parent (SpineDBEditor)
            entity_class (dict)
            entities (list(list(str))
            db_mngr (SpineDBManager)
            *db_maps: DatabaseMapping instances
        """
        super().__init__(parent, db_mngr)
        self._commit_data = commit_data
        self.entity_class = entity_class
        self.entities = entities
        self.db_maps = db_maps
        self.table_view.horizontalHeader().setMinimumSectionSize(0)
        self.setWindowTitle("Add '{0}' entities".format(self.entity_class["name"]))
        self.populate_table_view()
        self.connect_signals()

    def _populate_layout(self):
        label = QLabel("<p>Please check the entities you want to add and press <b>Ok</b>.</p>")
        label.setWordWrap(True)
        self.layout().addWidget(label)
        super()._populate_layout()

    def make_table_view(self):
        return QTableWidget(self)

    def populate_table_view(self):
        dimension_name_list = self.entity_class["dimension_name_list"]
        self.table_view.setRowCount(len(self.entities))
        self.table_view.setColumnCount(len(dimension_name_list) + 1)
        labels = ("",) + dimension_name_list
        self.table_view.setHorizontalHeaderLabels(labels)
        self.table_view.verticalHeader().hide()
        for row, entity in enumerate(self.entities):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsEnabled)
            item.setCheckState(Qt.CheckState.Checked)
            self.table_view.setItem(row, 0, item)
            for column, element_byname in enumerate(entity):
                item = QTableWidgetItem(DB_ITEM_SEPARATOR.join(element_byname))
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
        check_state = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
        item.setCheckState(check_state)

    def _handle_table_view_current_changed(self, current, _previous):
        if current.isValid():
            self.table_view.selectionModel().clearCurrentIndex()

    @Slot()
    def accept(self):
        """Collect info from dialog and try to add items."""
        if not self._commit_data:
            super().accept()
            return
        db_map_data = self.get_db_map_data()
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to add")
            return
        self.db_mngr.add_entities(db_map_data)
        super().accept()

    def get_db_map_data(self):
        data = []
        for row in range(self.table_view.rowCount()):
            if self.table_view.item(row, 0).checkState() != Qt.CheckState.Checked:
                continue
            element_byname_list = tuple(self.entities[row])
            byname = tuple(x for byname in element_byname_list for x in byname)
            data.append({"entity_class_name": self.entity_class["name"], "entity_byname": byname})
        return {db_map: data for db_map in self.db_maps}


class AddItemsDialog(ManageItemsDialog):
    """A dialog to query user's preferences for new db items."""

    def __init__(self, parent, db_mngr, *db_maps):
        """
        Args:
            parent (SpineDBEditor)
            db_mngr (SpineDBManager)
            *db_maps: DiffDatabaseMapping instances
        """
        super().__init__(parent, db_mngr)
        self.db_maps = db_maps
        self.keyed_db_maps = {x.codename: x for x in db_maps}
        self.remove_rows_button = QToolButton(self)
        self.remove_rows_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.remove_rows_button.setText("Remove selected rows")

    def _populate_layout(self):
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


class AddEntityClassesDialog(ShowIconColorEditorMixin, GetEntityClassesMixin, AddItemsDialog):
    """A dialog to query user's preferences for new entity classes."""

    def __init__(self, parent, item, db_mngr, *db_maps, force_default=False):
        """
        Args:
            parent (SpineDBEditor)
            item (MultiDBTreeItem)
            db_mngr (SpineDBManager)
            *db_maps: DatabaseMapping instances
            force_default (bool): if True, defaults are non-editable
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.setWindowTitle("Add entity classes")
        self.table_view.set_column_converter_for_pasting("display icon", string_to_display_icon)
        self.table_view.set_column_converter_for_pasting("active by default", string_to_bool)
        self.model = EmptyRowModel(self)
        self.model.force_default = force_default
        self.table_view.setModel(self.model)
        self.dimension_count_widget = QWidget(self)
        layout = QHBoxLayout(self.dimension_count_widget)
        layout.addWidget(QLabel("Number of dimensions"))
        self.spin_box = QSpinBox(self)
        self.spin_box.setMinimum(0)
        layout.addWidget(self.spin_box)
        layout.addStretch()
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.table_view.setItemDelegate(ManageEntityClassesDelegate(self))
        dimension_one_name = item.name if item.item_type != "root" else None
        self.number_of_dimensions = 1 if dimension_one_name is not None else 0
        self.spin_box.setValue(self.number_of_dimensions)
        self.connect_signals()
        labels = ["dimension name (1)"] if dimension_one_name is not None else []
        labels += ["entity class name", "description", "display icon", "active by default", "databases"]
        self.model.set_horizontal_header_labels(labels)
        db_names = ",".join(x.codename for x in item.db_maps)
        self.default_display_icon = None
        self.model.set_default_row(
            **{
                "dimension name (1)": dimension_one_name,
                "display icon": self.default_display_icon,
                "active by default": self.number_of_dimensions != 0,
                "databases": db_names,
            }
        )
        self.model.clear()

    def _populate_layout(self):
        self.layout().addWidget(self.dimension_count_widget, 0, 0, 1, -1)
        self.layout().addWidget(self.table_view, 1, 0)
        self.layout().addWidget(self.remove_rows_button, 2, 0)
        self.layout().addWidget(self.button_box, 3, 0, -1, -1)

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        self.spin_box.valueChanged.connect(self._handle_spin_box_value_changed)
        # pylint: disable=unnecessary-lambda
        self.table_view.itemDelegate().icon_color_editor_requested.connect(
            lambda index: self.show_icon_color_editor(index)
        )

    @Slot(int)
    def _handle_spin_box_value_changed(self, i):
        self.spin_box.setEnabled(False)
        if i > self.number_of_dimensions:
            self.insert_column()
        elif i < self.number_of_dimensions:
            self.remove_column()
        default_value = self.number_of_dimensions != 0
        self.model.default_row["active by default"] = default_value
        column = self.model.horizontal_header_labels().index("active by default")
        last_row = self.model.rowCount() - 1
        index = self.model.index(last_row, column)
        if index.data() != default_value:
            self.model.setData(index, default_value)
        self.spin_box.setEnabled(True)
        self.resize_window_to_columns()

    def insert_column(self):
        column = self.number_of_dimensions
        self.number_of_dimensions += 1
        column_name = "dimension name ({0})".format(self.number_of_dimensions)
        self.model.insertColumns(column, 1)
        self.model.insert_horizontal_header_labels(column, [column_name])
        self.table_view.resizeColumnToContents(column)

    def remove_column(self):
        self.number_of_dimensions -= 1
        column = self.number_of_dimensions
        self.model.header.pop(column)
        self.model.removeColumns(column, 1)

    @Slot(QModelIndex, QModelIndex, list)
    def _handle_model_data_changed(self, top_left, bottom_right, roles):
        if Qt.ItemDataRole.EditRole not in roles:
            return
        left = top_left.column()
        if left >= self.number_of_dimensions:
            return
        right = bottom_right.column()
        if right >= self.number_of_dimensions:
            return
        top = top_left.row()
        bottom = bottom_right.row()
        for row in range(top, bottom + 1):
            obj_cls_names = [
                name for j in range(self.number_of_dimensions) if (name := self.model.index(row, j).data())
            ]
            relationship_class_name = name_from_dimensions(obj_cls_names)
            self.model.setData(self.model.index(row, self.number_of_dimensions), relationship_class_name)

    @Slot()
    def accept(self):
        """Collect info from dialog and try to add items."""
        db_map_data = dict()
        header_labels = self.model.horizontal_header_labels()
        name_column = header_labels.index("entity class name")
        description_column = header_labels.index("description")
        display_icon_column = header_labels.index("display icon")
        active_by_default_column = header_labels.index("active by default")
        db_column = header_labels.index("databases")
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            entity_class_name = row_data[name_column]
            if not entity_class_name:
                self.parent().msg_error.emit("Entity class missing at row {}".format(i + 1))
                return
            description = row_data[description_column]
            display_icon = row_data[display_icon_column]
            if not display_icon:
                display_icon = self.default_display_icon
            active_by_default = row_data[active_by_default_column]
            pre_item = {
                "name": entity_class_name,
                "description": description,
                "display_icon": display_icon,
                "active_by_default": active_by_default,
            }
            db_names = row_data[db_column]
            if db_names is None:
                db_names = ""
            for db_name in db_names.split(","):
                if db_name not in self.keyed_db_maps:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(db_name, i + 1))
                    return
                db_map = self.keyed_db_maps[db_name]
                entity_classes = self.db_map_ent_cls_lookup_by_name[db_map]
                dimension_id_list = list()
                for column in range(name_column):  # Leave 'name' column outside
                    dimension_name = row_data[column]
                    if dimension_name not in entity_classes:
                        self.parent().msg_error.emit(
                            "Invalid dimension '{}' for db '{}' at row {}".format(dimension_name, db_name, i + 1)
                        )
                        return
                    dimension_id = entity_classes[dimension_name]["id"]
                    dimension_id_list.append(dimension_id)
                item = pre_item.copy()
                item["dimension_id_list"] = dimension_id_list
                db_map_data.setdefault(db_map, []).append(item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to add")
            return
        self.db_mngr.add_entity_classes(db_map_data)
        super().accept()


class AddEntitiesOrManageElementsDialog(GetEntityClassesMixin, GetEntitiesMixin, AddItemsDialog):
    """A dialog to query user's preferences for new entities."""

    def __init__(self, parent, db_mngr, *db_maps):
        """
        Args:
            parent (SpineDBEditor)
            db_mngr (SpineDBManager)
            *db_maps: DatabaseMapping instances
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.model = self.make_model()
        self.table_view.setModel(self.model)
        self.header_widget = QWidget(self)
        layout = QHBoxLayout(self.header_widget)
        layout.addWidget(QLabel("Entity class"))
        self.ent_cls_combo_box = QComboBox(self)
        layout.addWidget(self.ent_cls_combo_box)
        layout.addStretch()
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.entity_class_keys = None

    def _class_key_to_str(self, key, *db_maps):
        raise NotImplementedError()

    def _accepts_class(self, ent_cls):
        """Returns whether the widget should handle the given entity class.

        Args:
            ent_cls (MappedItem)

        Returns:
            bool
        """
        raise NotImplementedError()

    def make_model(self):
        raise NotImplementedError()

    def _do_reset_model(self):
        raise NotImplementedError()

    @Slot(int)
    def reset_model(self, index):
        """Setup model according to current entity class selected in combobox."""
        self.class_key = self.entity_class_keys[index]
        self._do_reset_model()

    def _populate_layout(self):
        self.layout().addWidget(self.header_widget, 0, 0, 1, -1)
        self.layout().addWidget(self.table_view, 1, 0)
        self.layout().addWidget(self.remove_rows_button, 2, 0)
        self.layout().addWidget(self.button_box, 3, 0, -1, -1)

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        self.ent_cls_combo_box.currentIndexChanged.connect(self.reset_model)

    @Slot(QModelIndex, QModelIndex, list)
    def _handle_model_data_changed(self, top_left, bottom_right, roles):
        if roles and Qt.ItemDataRole.EditRole not in roles or self.entity_class is None:
            return
        dimension_count = len(self.dimension_name_list)
        if dimension_count == 0:
            return
        header = self.model.horizontal_header_labels()
        left = top_left.column()
        right = bottom_right.column()
        if left <= header.index("entity name") <= right:
            return
        if "databases" in header and left == right == header.index("databases"):
            return
        top = top_left.row()
        bottom = bottom_right.row()
        for row in range(top, bottom + 1):
            el_names = [n for n in (self.model.index(row, j).data() for j in range(dimension_count)) if n]
            entity_name = name_from_elements(el_names)
            self.model.setData(self.model.index(row, dimension_count), entity_name)


class AddEntitiesDialog(AddEntitiesOrManageElementsDialog):
    """A dialog to query user's preferences for new entities."""

    def __init__(self, parent, item, db_mngr, *db_maps, force_default=False, commit_data=True):
        """
        Args:
            parent (SpineDBEditor)
            item (MultiDBTreeItem)
            db_mngr (SpineDBManager)
            *db_maps: DatabaseMapping instances
            force_default (bool): if True, defaults are non-editable
        """
        super().__init__(parent, db_mngr, *db_maps)
        self._commit_data = commit_data
        self.entity_names_by_class_name = {}
        if item.item_type == "entity":
            entity_name = item.name
            entity_class_name = item.parent_item.name
            self.entity_names_by_class_name = {entity_class_name: entity_name}
            if item.parent_item.item_type == "entity_class":
                self.class_key = item.parent_item.display_id
        elif item.item_type == "entity_class":
            self.class_key = item.display_id
        self.model.force_default = force_default
        self.setWindowTitle("Add entities")
        self.table_view.setItemDelegate(ManageEntitiesDelegate(self))
        self.ent_cls_combo_box.setEnabled(not force_default)
        db_maps_by_keys = {}
        for db_map, entity_classes in self.db_map_ent_cls_lookup.items():
            for key, ent_cls in entity_classes.items():
                if self._accepts_class(ent_cls):
                    db_maps_by_keys.setdefault(key, set()).add(db_map)

        self.entity_class_keys = sorted(db_maps_by_keys)
        self.ent_cls_combo_box.addItems(
            [self._class_key_to_str(key, *db_maps_by_keys[key]) for key in self.entity_class_keys]
        )
        try:
            current_index = self.entity_class_keys.index(self.class_key)
            self.reset_model(current_index)
            self._handle_model_reset()
        except ValueError:
            current_index = -1
        self.ent_cls_combo_box.setCurrentIndex(current_index)
        self.connect_signals()

    def _class_key_to_str(self, key, *db_maps):
        class_name = self.db_map_ent_cls_lookup[db_maps[0]][key]["name"]
        if len(db_maps) == len(self.db_maps):
            return class_name
        return class_name + "@(" + ", ".join(db_map.codename for db_map in db_maps) + ")"

    def _accepts_class(self, ent_cls):
        if self.entity_class is None:
            return True
        if self.entity_class["dimension_name_list"]:
            # Base class is multidimensional, check if given ent_cls containts the base in its entirety
            return set(ent_cls["dimension_name_list"]) >= set(self.entity_class["dimension_name_list"])
        # Base class is zero-dimensional, check if given ent_cls containts it
        return self.entity_class["name"] in set(ent_cls["dimension_name_list"]) | {ent_cls["name"]}

    def make_model(self):
        return EmptyRowModel(self)

    def _do_reset_model(self):
        header = self.dimension_name_list + ("entity name", "databases")
        self.model.set_horizontal_header_labels(header)
        default_db_maps = [db_map for db_map, keys in self.db_map_ent_cls_lookup.items() if self.class_key in keys]
        db_names = ",".join([db_name for db_name, db_map in self.keyed_db_maps.items() if db_map in default_db_maps])
        defaults = {"databases": db_names}
        defaults.update(self.entity_names_by_class_name)
        self.model.set_default_row(**defaults)
        self.model.clear()

    def get_db_map_data(self):
        db_map_data = {}
        name_column = self.model.horizontal_header_labels().index("entity name")
        db_column = self.model.horizontal_header_labels().index("databases")
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            element_byname_list = [row_data[column] for column in range(name_column)]
            entity_name = row_data[name_column]
            if not entity_name:
                self.parent().msg_error.emit(f"Entity missing at row {i + 1}")
                return
            pre_item = {"name": entity_name}
            db_names = row_data[db_column]
            if db_names is None:
                db_names = ""
            for db_name in db_names.split(","):
                if db_name not in self.keyed_db_maps:
                    self.parent().msg_error.emit(f"Invalid database {db_name} at row {i + 1}")
                    return
                db_map = self.keyed_db_maps[db_name]
                entity_classes = self.db_map_ent_cls_lookup[db_map]
                ent_cls = entity_classes[self.class_key]
                class_id = ent_cls["id"]
                dimension_id_list = ent_cls["dimension_id_list"]
                entities = self.db_map_ent_lookup[db_map]
                element_id_list = []
                for entity_class_id, element_byname in zip(dimension_id_list, element_byname_list):
                    if (entity_class_id, element_byname) not in entities:
                        self.parent().msg_error.emit(
                            f"Invalid element '{element_byname}' for db '{db_name}' at row {i + 1}"
                        )
                        return
                    element_id = entities[entity_class_id, element_byname]["id"]
                    element_id_list.append(element_id)
                item = pre_item.copy()
                item.update({"element_id_list": element_id_list, "class_id": class_id})
                db_map_data.setdefault(db_map, []).append(item)
        return db_map_data

    @Slot()
    def accept(self):
        """Collect info from dialog and try to add items."""
        if not self._commit_data:
            super().accept()
            return
        db_map_data = self.get_db_map_data()
        if db_map_data is None:
            return
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to add")
            return
        self.db_mngr.add_entities(db_map_data)
        super().accept()


class ManageElementsDialog(AddEntitiesOrManageElementsDialog):
    """A dialog to query user's preferences for managing entity dimensions."""

    def __init__(self, parent, item, db_mngr, *db_maps):
        """
        Args:
            parent (SpineDBEditor): data store widget
            item (MultiDBTreeItem)
            db_mngr (SpineDBManager): the manager to do the removal
            *db_maps: DatabaseMapping instances
        """
        super().__init__(parent, db_mngr, *db_maps)
        if item.item_type == "entity_class":
            self.class_key = item.display_id
        self.setWindowTitle("Manage elements")
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.remove_rows_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.remove_rows_button.setToolTip("<p>Remove selected entities.</p>")
        self.remove_rows_button.setIconSize(QSize(24, 24))
        self.db_map = db_maps[0]
        self.entity_ids = {}
        layout = self.header_widget.layout()
        self.db_combo_box = QComboBox(self)
        layout.addSpacing(32)
        layout.addWidget(QLabel("Database", self))
        layout.addWidget(self.db_combo_box)
        self.splitter = QSplitter(self)
        self.splitter.setChildrenCollapsible(False)
        self.add_button = QToolButton(self)
        self.add_button.setToolTip("<p>Add entities by combining selected available elements.</p>")
        self.add_button.setIcon(QIcon(":/icons/menu_icons/cubes_plus.svg"))
        self.add_button.setIconSize(QSize(24, 24))
        self.add_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.add_button.setText(">>")
        self._label_available = QLabel("Available elements", self)
        self._label_existing = QLabel("Existing entities", self)
        self.hidable_widgets = [
            self.add_button,
            self._label_available,
            self._label_existing,
            self.table_view,
            self.remove_rows_button,
        ]
        for widget in self.hidable_widgets:
            widget.hide()
        self.existing_items_model = MinimalTableModel(self, lazy=False)
        self.new_items_model = MinimalTableModel(self, lazy=False)
        self.model.sub_models = [self.new_items_model, self.existing_items_model]
        self.db_combo_box.addItems([db_map.codename for db_map in db_maps])
        self.reset_entity_class_combo_box(db_maps[0].codename)
        self.connect_signals()

    def _populate_layout(self):
        self.layout().addWidget(self.header_widget, 0, 0, 1, 4, Qt.AlignHCenter)
        self.layout().addWidget(self._label_available, 1, 0)
        self.layout().addWidget(self._label_existing, 1, 2)
        self.layout().addWidget(self.splitter, 2, 0)
        self.layout().addWidget(self.add_button, 2, 1)
        self.layout().addWidget(self.table_view, 2, 2)
        self.layout().addWidget(self.remove_rows_button, 2, 3)
        self.layout().addWidget(self.button_box, 3, 0, -1, -1)

    def make_model(self):
        return CompoundTableModel(self)

    def splitter_widgets(self):
        return [self.splitter.widget(i) for i in range(self.splitter.count())]

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        self.db_combo_box.currentTextChanged.connect(self.reset_entity_class_combo_box)
        self.add_button.clicked.connect(self.add_entities)

    def _accepts_class(self, ent_cls):
        return bool(ent_cls["dimension_id_list"])

    def _class_key_to_str(self, key, *_db_maps):
        return self.db_map_ent_cls_lookup[self.db_map][key]["name"]

    @Slot(str)
    def reset_entity_class_combo_box(self, database):
        self.db_map = self.keyed_db_maps[database]
        self.entity_class_keys = [
            key for key, ent_cls in self.db_map_ent_cls_lookup[self.db_map].items() if self._accepts_class(ent_cls)
        ]
        self.ent_cls_combo_box.addItems([self._class_key_to_str(key) for key in self.entity_class_keys])
        try:
            current_index = self.entity_class_keys.index(self.class_key)
            self.reset_model(current_index)
            self._handle_model_reset()
        except ValueError:
            current_index = -1
        self.ent_cls_combo_box.setCurrentIndex(current_index)

    @Slot(bool)
    def add_entities(self, checked=True):
        element_names = [[item.text(0) for item in wg.selectedItems()] for wg in self.splitter_widgets()]
        candidate = set(product(*element_names))
        existing = {
            tuple(elements[:-1]) for elements in self.new_items_model._main_data + self.existing_items_model._main_data
        }
        to_add = candidate - existing
        count = len(to_add)
        if not count:
            return
        self.new_items_model.insertRows(0, count)
        self.new_items_model._main_data[0:count] = [list(row) + [""] for row in to_add]
        self.model.refresh()
        self.model.dataChanged.emit(self.model.index(0, 0), self.model.index(count - 1, self.model.columnCount() - 2))

    def _do_reset_model(self):
        horizontal_header_labels = self.dimension_name_list + ("entity name",)
        self.model.set_horizontal_header_labels(horizontal_header_labels)
        self.existing_items_model.set_horizontal_header_labels(horizontal_header_labels)
        self.new_items_model.set_horizontal_header_labels(horizontal_header_labels)
        self.entity_ids.clear()
        for db_map in self.db_maps:
            entity_classes = self.db_map_ent_cls_lookup[db_map]
            ent_cls = entity_classes.get(self.class_key, None)
            if ent_cls is None:
                continue
            for entity in self.db_mngr.get_items_by_field(db_map, "entity", "class_id", ent_cls["id"]):
                key = tuple(DB_ITEM_SEPARATOR.join(byname) for byname in entity["element_byname_list"]) + (
                    entity["name"],
                )
                self.entity_ids[key] = entity["id"]
        existing_items = sorted(self.entity_ids)
        self.existing_items_model.reset_model(existing_items)
        self.model.refresh()
        self.model.modelReset.emit()
        for wg in self.splitter_widgets():
            wg.deleteLater()
        for name in self.dimension_name_list:
            tree_widget = QTreeWidget(self)
            tree_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            tree_widget.setColumnCount(1)
            tree_widget.setIndentation(0)
            header_item = QTreeWidgetItem([name])
            header_item.setTextAlignment(0, Qt.AlignHCenter)
            tree_widget.setHeaderItem(header_item)
            elements = [
                x
                for k in ("entity_class_name", "superclass_name")
                for x in self.db_mngr.get_items_by_field(self.db_map, "entity", k, name)
            ]
            items = [QTreeWidgetItem([DB_ITEM_SEPARATOR.join(el["entity_byname"])]) for el in elements]
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
        to_remove = set()
        to_update = []
        new_name_by_element_byname_list = {tuple(row[:-1]): row[-1] for row in self.existing_items_model._main_data}
        for key, id_ in self.entity_ids.items():
            element_byname_list, old_name = key[:-1], key[-1]
            new_name = new_name_by_element_byname_list.get(element_byname_list)
            if new_name is None:
                to_remove.add(id_)
            elif old_name != new_name:
                to_update.append({"id": id_, "name": new_name})
        to_add = [
            {
                "entity_class_name": self.class_name,
                "entity_byname": tuple(x for byname in row[:-1] for x in byname.split(DB_ITEM_SEPARATOR)),
                "name": row[-1],
            }
            for row in self.new_items_model._main_data
        ]
        identifier = self.db_mngr.get_command_identifier()
        self.db_mngr.remove_items({self.db_map: {"entity": to_remove}}, identifier=identifier)
        self.db_mngr.update_items("entity", {self.db_map: to_update}, identifier=identifier)
        self.db_mngr.add_items("entity", {self.db_map: to_add}, identifier=identifier)
        super().accept()


class EntityGroupDialogBase(QDialog):
    def __init__(self, parent, entity_class_item, db_mngr, *db_maps):
        """
        Args:
            parent (SpineDBEditor): data store widget
            entity_class_item (EntityClassItem)
            db_mngr (SpineDBManager)
            *db_maps: database mappings
        """
        super().__init__(parent)
        self.entity_class_item = entity_class_item
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self.db_map = db_maps[0]
        self.db_maps_by_codename = {db_map.codename: db_map for db_map in db_maps}
        self.db_combo_box = QComboBox(self)
        self.header_widget = QWidget(self)
        self.group_name_line_edit = QLineEdit(self)
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.addWidget(QLabel("Group name:"))
        header_layout.addWidget(self.group_name_line_edit)
        header_layout.addSpacing(32)
        header_layout.addWidget(QLabel("Database"))
        header_layout.addWidget(self.db_combo_box)
        self.non_members_tree = QTreeWidget(self)
        self.non_members_tree.setHeaderLabel("Non members")
        self.non_members_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.non_members_tree.setColumnCount(1)
        self.non_members_tree.setIndentation(0)
        self.members_tree = QTreeWidget(self)
        self.members_tree.setHeaderLabel("Members")
        self.members_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
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
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        layout = QGridLayout(self)
        layout.addWidget(self.header_widget, 0, 0, 1, 3, Qt.AlignHCenter)
        layout.addWidget(self.non_members_tree, 1, 0)
        layout.addWidget(self.vertical_button_widget, 1, 1)
        layout.addWidget(self.members_tree, 1, 2)
        layout.addWidget(self.button_box, 2, 0, 1, 3)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.db_combo_box.addItems(list(self.db_maps_by_codename))
        self.db_map_entity_ids = {
            db_map: {
                x["name"]: x["id"]
                for x in self.db_mngr.get_items_by_field(
                    self.db_map, "entity", "class_id", self.entity_class_item.db_map_id(db_map)
                )
            }
            for db_map in db_maps
        }

    def connect_signals(self):
        """Connect signals to slots."""
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.db_combo_box.currentTextChanged.connect(self.reset_list_widgets)
        self.add_button.clicked.connect(self.add_members)
        self.remove_button.clicked.connect(self.remove_members)

    def reset_list_widgets(self, database):
        self.db_map = self.db_maps_by_codename[database]
        entity_ids = self.db_map_entity_ids[self.db_map]
        members = []
        non_members = []
        for ent_name in sorted(entity_ids):
            ent_id = entity_ids[ent_name]
            if ent_id in self.initial_member_ids():
                members.append(ent_name)
            elif ent_id != self.initial_entity_id():
                non_members.append(ent_name)
        member_items = [QTreeWidgetItem([ent_name]) for ent_name in members]
        non_member_items = [QTreeWidgetItem([ent_name]) for ent_name in non_members]
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
            self.parent().msg_error.emit("Please select at least one member entity.")
            return False
        return True


class AddEntityGroupDialog(EntityGroupDialogBase):
    def __init__(self, parent, entity_class_item, db_mngr, *db_maps):
        """
        Args:
            parent (SpineDBEditor): data store widget
            entity_class_item (EntityClassItem)
            db_mngr (SpineDBManager)
            *db_maps: database mappings
        """
        super().__init__(parent, entity_class_item, db_mngr, *db_maps)
        self.setWindowTitle("Add entity group")
        self.group_name_line_edit.setFocus()
        self.group_name_line_edit.setPlaceholderText("Type group name here")
        self.reset_list_widgets(db_maps[0].codename)
        self.connect_signals()

    def initial_member_ids(self):
        return set()

    def initial_entity_id(self):
        return None

    def _check_validity(self):
        if not super()._check_validity():
            return False
        group_name = self.group_name_line_edit.text()
        if not group_name:
            self.parent().msg_error.emit("Please enter a name for the group.")
            return False
        if group_name in self.db_map_entity_ids[self.db_map]:
            self.parent().msg_error.emit(
                f"An entity called {group_name} already exists in this class. Please select a different group name."
            )
            return False
        return True

    @Slot()
    def accept(self):
        if not self._check_validity():
            return
        class_name = self.entity_class_item.name
        group_name = self.group_name_line_edit.text()
        member_names = {item.text(0) for item in self.members_tree.findItems("*", Qt.MatchWildcard)}
        db_map_data = {
            self.db_map: {
                "entities": [(class_name, group_name)],
                "entity_groups": [
                    (self.entity_class_item.name, group_name, member_name) for member_name in member_names
                ],
            }
        }
        self.db_mngr.import_data(db_map_data, command_text="Add entity group")
        super().accept()


class ManageMembersDialog(EntityGroupDialogBase):
    def __init__(self, parent, entity_item, db_mngr, *db_maps):
        """
        Args:
            parent (SpineDBEditor): data store widget
            entity_item (entity_tree_item.EntityItem)
            db_mngr (SpineDBManager)
            *db_maps: database mappings
        """
        super().__init__(parent, entity_item.parent_item, db_mngr, *db_maps)
        self.setWindowTitle("Manage members")
        self.group_name_line_edit.setReadOnly(True)
        self.group_name_line_edit.setText(entity_item.name)
        self.entity_item = entity_item
        self.reset_list_widgets(db_maps[0].codename)
        self.connect_signals()

    def _entity_groups(self):
        return self.db_mngr.get_items_by_field(self.db_map, "entity_group", "group_id", self.initial_entity_id())

    def initial_member_ids(self):
        return {x["member_id"] for x in self._entity_groups()}

    def initial_entity_id(self):
        return self.entity_item.db_map_id(self.db_map)

    @Slot()
    def accept(self):
        if not self._check_validity():
            return
        ent = self.entity_item.db_map_data(self.db_map)
        current_member_ids = {
            self.db_map_entity_ids[self.db_map][item.text(0)]
            for item in self.members_tree.findItems("*", Qt.MatchWildcard)
        }
        added = current_member_ids - self.initial_member_ids()
        removed = self.initial_member_ids() - current_member_ids
        items_to_add = [
            {"entity_id": ent["id"], "entity_class_id": ent["class_id"], "member_id": member_id} for member_id in added
        ]
        ids_to_remove = [x["id"] for x in self._entity_groups() if x["member_id"] in removed]
        identifier = self.db_mngr.get_command_identifier()
        if items_to_add:
            self.db_mngr.add_items("entity_group", {self.db_map: items_to_add}, identifier=identifier)
        if ids_to_remove:
            self.db_mngr.remove_items({self.db_map: {"entity_group": ids_to_remove}}, identifier=identifier)
        super().accept()
