######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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

"""

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
from ...mvcmodels.empty_row_model import EmptyRowModel
from ...mvcmodels.compound_table_model import CompoundTableModel
from ...mvcmodels.minimal_table_model import MinimalTableModel
from .custom_delegates import ManageEntityClassesDelegate, ManageEntitiesDelegate
from .manage_items_dialogs import (
    ShowIconColorEditorMixin,
    GetEntityClassesMixin,
    GetEntitiesMixin,
    ManageItemsDialog,
    ManageItemsDialogBase,
)
from ...spine_db_commands import SpineDBMacro, AddItemsCommand, RemoveItemsCommand


class AddReadyEntitiesDialog(ManageItemsDialogBase):
    """A dialog to let the user add new 'ready' relationships."""

    def __init__(self, parent, entity_class, entities, db_mngr, *db_maps):
        """
        Args:
            parent (SpineDBEditor)
            entity_class (dict)
            entities (list(list(str))
            db_mngr (SpineDBManager)
            *db_maps: DiffDatabaseMapping instances
        """
        super().__init__(parent, db_mngr)
        self.entity_class = entity_class
        self.entities = entities
        self.db_maps = db_maps
        label = QLabel("<p>Please check the entities you want to add and press <b>Ok</b>.</p>")
        label.setWordWrap(True)
        self.table_view.horizontalHeader().setMinimumSectionSize(0)
        self.layout().addWidget(label, 0, 0)
        self.layout().addWidget(self.table_view, 1, 0)
        self.layout().addWidget(self.button_box, 2, 0, -1, -1)
        self.setWindowTitle("Add '{0}' entities".format(self.entity_class["name"]))
        self.populate_table_view()
        self.connect_signals()

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
            for column, element_name in enumerate(entity):
                item = QTableWidgetItem(element_name)
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

    def accept(self):
        super().accept()
        data = []
        for row in range(self.table_view.rowCount()):
            if self.table_view.item(row, 0).checkState() != Qt.CheckState.Checked:
                continue
            entities = self.entities[row]
            data.append([self.entity_class["name"], entities])
        db_map_data = {db_map: {"entities": data} for db_map in self.db_maps}
        self.db_mngr.import_data(db_map_data, command_text="Add entities")


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
        self.remove_rows_button = QToolButton()
        self.remove_rows_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.remove_rows_button.setText("Remove selected rows")
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
            *db_maps: DiffDatabaseMapping instances
            force_default (bool): if True, defaults are non-editable
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.setWindowTitle("Add entity classes")
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
        self.layout().addWidget(self.dimension_count_widget, 0, 0, 1, -1)
        self.layout().addWidget(self.table_view, 1, 0)
        self.layout().addWidget(self.remove_rows_button, 2, 0)
        self.layout().addWidget(self.button_box, 3, 0, -1, -1)
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.table_view.setItemDelegate(ManageEntityClassesDelegate(self))
        dimension_one_name = item.display_data if item.item_type != "root" else None
        self.number_of_dimensions = 1 if dimension_one_name is not None else 0
        self.spin_box.setValue(self.number_of_dimensions)
        self.connect_signals()
        labels = ['dimension name (1)'] if dimension_one_name is not None else []
        labels += ['entity class name', 'description', 'display icon', 'databases']
        self.model.set_horizontal_header_labels(labels)
        self.db_map_ent_cls_lookup_by_name = self.make_db_map_ent_cls_lookup_by_name()
        db_names = ",".join(x.codename for x in item.db_maps)
        self.default_display_icon = None
        self.model.set_default_row(
            **{
                'dimension name (1)': dimension_one_name,
                'display_icon': self.default_display_icon,
                'databases': db_names,
            }
        )
        self.model.clear()

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
        top = top_left.row()
        left = top_left.column()
        bottom = bottom_right.row()
        right = bottom_right.column()
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                if column >= self.number_of_dimensions:
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
        name_column = self.model.horizontal_header_labels().index("entity class name")
        description_column = self.model.horizontal_header_labels().index("description")
        display_icon_column = self.model.horizontal_header_labels().index("display icon")
        db_column = self.model.horizontal_header_labels().index("databases")
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
            pre_item = {'name': entity_class_name, 'description': description, 'display_icon': display_icon}
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
                item['dimension_id_list'] = dimension_id_list
                db_map_data.setdefault(db_map, []).append(item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to add")
            return
        self.db_mngr.add_entity_classes(db_map_data)
        super().accept()


class AddEntitiesOrManageElementsDialog(GetEntityClassesMixin, GetEntitiesMixin, AddItemsDialog):
    """A dialog to query user's preferences for new relationships."""

    def __init__(self, parent, db_mngr, *db_maps):
        """
        Args:
            parent (SpineDBEditor)
            db_mngr (SpineDBManager)
            *db_maps: DiffDatabaseMapping instances
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
        self.layout().addWidget(self.header_widget, 0, 0, 1, -1)
        self.layout().addWidget(self.table_view, 1, 0)
        self.layout().addWidget(self.remove_rows_button, 2, 0)
        self.layout().addWidget(self.button_box, 3, 0, -1, -1)
        self.remove_rows_button.setIcon(QIcon(":/icons/menu_icons/cube_minus.svg"))
        self.db_map_ent_lookup = self.make_db_map_ent_lookup()
        self.db_map_alt_id_lookup = self.make_db_map_alt_id_lookup()
        self.db_map_ent_cls_lookup = self.make_db_map_ent_cls_lookup()
        self.entity_class_keys = []
        self.class_name = None
        self.dimension_name_list = None

    def make_model(self):
        raise NotImplementedError()

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        self.ent_cls_combo_box.currentIndexChanged.connect(self.reset_model)

    @Slot(int)
    def reset_model(self, index):
        """Called when relationship_class's combobox's index changes.
        Update relationship_class attribute accordingly and reset model."""
        raise NotImplementedError()


class AddEntitiesDialog(AddEntitiesOrManageElementsDialog):
    """A dialog to query user's preferences for new relationships."""

    def __init__(self, parent, item, db_mngr, *db_maps, force_default=False):
        """
        Args:
            parent (SpineDBEditor)
            item (MultiDBTreeItem)
            db_mngr (SpineDBManager)
            *db_maps: DiffDatabaseMapping instances
            force_default (bool): if True, defaults are non-editable
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.entity_names_by_class_name = {}
        if item.item_type == "entity":
            if not item.element_name_list:
                entity_name = item.display_data
                entity_class_name = item.parent_item.display_data
                self.entity_names_by_class_name = {entity_class_name: entity_name}
                entity_class_key = None
            else:
                entity_class_key = item.entity_class_key
        elif item.item_type == "entity_class":
            entity_class_key = item.display_id
        else:  # item_type == "root"
            entity_class_key = None
        self.entity_class = None
        self.model.force_default = force_default
        self.setWindowTitle("Add entities")
        self.table_view.setItemDelegate(ManageEntitiesDelegate(self))
        self.ent_cls_combo_box.setEnabled(not force_default)
        self.entity_class_keys = [
            key for entity_classes in self.db_map_ent_cls_lookup.values() for key in entity_classes
        ]
        self.ent_cls_combo_box.addItems(["{0} {1}".format(*key) for key in self.entity_class_keys])
        try:
            current_index = self.entity_class_keys.index(entity_class_key)
            self.reset_model(current_index)
            self._handle_model_reset()
        except ValueError:
            current_index = -1
        self.ent_cls_combo_box.setCurrentIndex(current_index)
        self.connect_signals()

    def make_model(self):
        return EmptyRowModel(self)

    @Slot(int)
    def reset_model(self, index):
        """Setup model according to current entity_class selected in combobox."""
        self.class_name, self.dimension_name_list = self.entity_class_keys[index]
        header = self.dimension_name_list + ('entity name', 'active alternatives', 'inactive alternatives', 'databases')
        self.model.set_horizontal_header_labels(header)
        default_db_maps = [
            db_map
            for db_map, ent_cls_list in self.db_map_ent_cls_lookup.items()
            if (self.class_name, self.dimension_name_list) in ent_cls_list
        ]
        db_names = ",".join([db_name for db_name, db_map in self.keyed_db_maps.items() if db_map in default_db_maps])
        defaults = {'active alternatives': 'Base', 'inactive alternatives': '', 'databases': db_names}
        defaults.update(self.entity_names_by_class_name)
        self.model.set_default_row(**defaults)
        self.model.clear()

    @Slot(QModelIndex, QModelIndex, list)
    def _handle_model_data_changed(self, top_left, bottom_right, roles):
        if Qt.ItemDataRole.EditRole not in roles:
            return
        header = self.model.horizontal_header_labels()
        top = top_left.row()
        left = top_left.column()
        bottom = bottom_right.row()
        right = bottom_right.column()
        dimension_count = len(self.dimension_name_list)
        for row in range(top, bottom + 1):
            if header.index('entity name') not in range(left, right + 1):
                col_data = lambda j: self.model.index(row, j).data()  # pylint: disable=cell-var-from-loop
                el_names = [col_data(j) for j in range(dimension_count) if col_data(j)]
                entity_name = self.class_name + "_"
                if len(el_names) == 1:
                    entity_name += el_names[0] + "__"
                else:
                    entity_name += "__".join(el_names)
                self.model.setData(self.model.index(row, dimension_count), entity_name)

    @Slot()
    def accept(self):
        """Collect info from dialog and try to add items."""
        db_map_data = dict()
        name_column = self.model.horizontal_header_labels().index("entity name")
        active_column = self.model.horizontal_header_labels().index("active alternatives")
        inactive_column = self.model.horizontal_header_labels().index("inactive alternatives")
        db_column = self.model.horizontal_header_labels().index("databases")
        for i in range(self.model.rowCount() - 1):  # last row will always be empty
            row_data = self.model.row_data(i)
            element_name_list = [row_data[column] for column in range(name_column)]
            entity_name = row_data[name_column]
            if not entity_name:
                self.parent().msg_error.emit("Entity missing at row {}".format(i + 1))
                return
            active_alts = [x for x in row_data[active_column].split(",") if x]
            inactive_alts = [x for x in row_data[inactive_column].split(",") if x]
            conflicting = set(active_alts) & set(inactive_alts)
            if conflicting:
                self.parent().msg_error.emit(f"Conflicting alternatives {conflicting} at row {i + 1}")
                return
            pre_item = {'name': entity_name}
            db_names = row_data[db_column]
            if db_names is None:
                db_names = ""
            for db_name in db_names.split(","):
                if db_name not in self.keyed_db_maps:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(db_name, i + 1))
                    return
                db_map = self.keyed_db_maps[db_name]
                entity_classes = self.db_map_ent_cls_lookup[db_map]
                if (self.class_name, self.dimension_name_list) not in entity_classes:
                    self.parent().msg_error.emit(
                        "Invalid entity class '{}' for db '{}' at row {}".format(self.class_name, db_name, i + 1)
                    )
                    return
                ent_cls = entity_classes[self.class_name, self.dimension_name_list]
                class_id = ent_cls["id"]
                dimension_id_list = ent_cls["dimension_id_list"]
                entities = self.db_map_ent_lookup[db_map]
                element_id_list = list()
                for entity_class_id, element_name in zip(dimension_id_list, element_name_list):
                    if (entity_class_id, element_name) not in entities:
                        self.parent().msg_error.emit(
                            "Invalid element '{}' for db '{}' at row {}".format(element_name, db_name, i + 1)
                        )
                        return
                    element_id = entities[entity_class_id, element_name]["id"]
                    element_id_list.append(element_id)
                active_alt_ids = []
                inactive_alt_ids = []
                alternative_ids = self.db_map_alt_id_lookup[db_map]
                for alt_name in active_alts:
                    if alt_name not in alternative_ids:
                        self.parent().msg_error.emit(
                            f"Invalid alternative '{alt_name}' for db '{db_name}' at row {i + 1}"
                        )
                        return
                    active_alt_ids.append(alternative_ids[alt_name])
                for alt_name in inactive_alts:
                    if alt_name not in alternative_ids:
                        self.parent().msg_error.emit(
                            f"Invalid alternative '{alt_name}' for db '{db_name}' at row {i + 1}"
                        )
                        return
                    inactive_alt_ids.append(alternative_ids[alt_name])
                item = pre_item.copy()
                item.update(
                    {
                        'element_id_list': element_id_list,
                        'class_id': class_id,
                        'active_alternative_id_list': active_alt_ids,
                        'inactive_alternative_id_list': inactive_alt_ids,
                    }
                )
                db_map_data.setdefault(db_map, []).append(item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to add")
            return
        self.db_mngr.add_entities(db_map_data)
        super().accept()


class ManageElementsDialog(AddEntitiesOrManageElementsDialog):
    """A dialog to query user's preferences for managing relationships."""

    def __init__(self, parent, item, db_mngr, *db_maps):
        """
        Args:
            parent (SpineDBEditor): data store widget
            item (MultiDBTreeItem)
            db_mngr (SpineDBManager): the manager to do the removal
            *db_maps: DiffDatabaseMapping instances
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.setWindowTitle("Manage elements")
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.remove_rows_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.remove_rows_button.setToolTip("<p>Remove selected entities.</p>")
        self.remove_rows_button.setIconSize(QSize(24, 24))
        self.db_map = db_maps[0]
        self.entity_ids = dict()
        layout = self.header_widget.layout()
        self.db_combo_box = QComboBox(self)
        layout.addSpacing(32)
        layout.addWidget(QLabel("Database"))
        layout.addWidget(self.db_combo_box)
        self.splitter = QSplitter(self)
        self.add_button = QToolButton(self)
        self.add_button.setToolTip("<p>Add entities by combining selected available elements.</p>")
        self.add_button.setIcon(QIcon(":/icons/menu_icons/cubes_plus.svg"))
        self.add_button.setIconSize(QSize(24, 24))
        self.add_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.add_button.setText(">>")
        label_available = QLabel("Available elements")
        label_existing = QLabel("Existing entities")
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
        self.reset_entity_class_combo_box(db_maps[0].codename, item.display_id)
        self.connect_signals()

    def make_model(self):
        return CompoundTableModel(self)

    def splitter_widgets(self):
        return [self.splitter.widget(i) for i in range(self.splitter.count())]

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        self.db_combo_box.currentTextChanged.connect(self.reset_entity_class_combo_box)
        self.add_button.clicked.connect(self.add_entities)

    @Slot(str)
    def reset_entity_class_combo_box(self, database, relationship_class_key=None):
        self.db_map = self.keyed_db_maps[database]
        self.entity_class_keys = list(self.db_map_ent_cls_lookup[self.db_map])
        self.ent_cls_combo_box.addItems([f"{name}" for name, _ in self.entity_class_keys])
        try:
            current_index = self.entity_class_keys.index(relationship_class_key)
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
            tuple(elements) for elements in self.new_items_model._main_data + self.existing_items_model._main_data
        }
        to_add = candidate - existing
        count = len(to_add)
        self.new_items_model.insertRows(0, count)
        self.new_items_model._main_data[0:count] = to_add
        self.model.refresh()

    @Slot(int)
    def reset_model(self, index):
        """Setup model according to current entity class selected in combobox."""
        self.class_name, self.dimension_name_list = self.entity_class_keys[index]
        self.model.set_horizontal_header_labels(self.dimension_name_list)
        self.existing_items_model.set_horizontal_header_labels(self.dimension_name_list)
        self.new_items_model.set_horizontal_header_labels(self.dimension_name_list)
        self.entity_ids.clear()
        for db_map in self.db_maps:
            entity_classes = self.db_map_ent_cls_lookup[db_map]
            ent_cls = entity_classes.get((self.class_name, self.dimension_name_list), None)
            if ent_cls is None:
                continue
            for entity in self.db_mngr.get_items_by_field(
                db_map, "entity", "class_id", ent_cls["id"], only_visible=False
            ):
                key = entity["element_name_list"]
                self.entity_ids[key] = entity["id"]
        existing_items = sorted(map(list, self.entity_ids))
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
            elements = self.db_mngr.get_items_by_field(self.db_map, "entity", "class_name", name, only_visible=False)
            items = [QTreeWidgetItem([el["name"]]) for el in elements]
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
        keys_to_remove = set(self.entity_ids) - {tuple(elements) for elements in self.existing_items_model._main_data}
        to_remove = [self.entity_ids[key] for key in keys_to_remove]
        self.db_mngr.remove_items({self.db_map: {"entity": to_remove}})
        to_add = [[self.class_name, element_name_list] for element_name_list in self.new_items_model._main_data]
        self.db_mngr.import_data({self.db_map: {"entities": to_add}}, command_text="Add entities")
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
                    self.db_map, "entity", "class_id", self.entity_class_item.db_map_id(db_map), only_visible=False
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
        class_name = self.entity_class_item.display_data
        group_name = self.group_name_line_edit.text()
        member_names = {item.text(0) for item in self.members_tree.findItems("*", Qt.MatchWildcard)}
        db_map_data = {
            self.db_map: {
                "entities": [(class_name, group_name)],
                "entity_groups": [
                    (self.entity_class_item.display_data, group_name, member_name) for member_name in member_names
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
        self.group_name_line_edit.setText(entity_item.display_data)
        self.entity_item = entity_item
        self.reset_list_widgets(db_maps[0].codename)
        self.connect_signals()

    def _entity_groups(self):
        return self.db_mngr.get_items_by_field(
            self.db_map, "entity_group", "group_id", self.initial_entity_id(), only_visible=False
        )

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
        child_cmds = []
        if items_to_add:
            cmd = AddItemsCommand(self.db_mngr, self.db_map, items_to_add, "entity_group")
            child_cmds.append(cmd)
        if ids_to_remove:
            cmd = RemoveItemsCommand(self.db_mngr, self.db_map, ids_to_remove, "entity_group")
            child_cmds.append(cmd)
        if child_cmds:
            macro = SpineDBMacro(iter(child_cmds))
            macro.setText(f"manage {self.entity_item.display_data}'s members")
            self.db_mngr.undo_stack[self.db_map].push(macro)
        super().accept()
