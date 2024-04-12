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

"""Classes for custom QDialogs to edit items in databases."""
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QComboBox, QTabWidget
from ..helpers import string_to_bool, string_to_display_icon
from ...mvcmodels.minimal_table_model import MinimalTableModel
from .custom_delegates import ManageEntityClassesDelegate, ManageEntitiesDelegate, RemoveEntitiesDelegate
from .manage_items_dialogs import (
    ShowIconColorEditorMixin,
    GetEntitiesMixin,
    GetEntityClassesMixin,
    ManageItemsDialog,
    DialogWithButtons,
)
from ...helpers import default_icon_id, DB_ITEM_SEPARATOR


class EditOrRemoveItemsDialog(ManageItemsDialog):
    def __init__(self, parent, db_mngr):
        super().__init__(parent, db_mngr)
        self.items = list()

    def all_databases(self, row):
        """Returns a list of db names available for a given row.
        Used by delegates.
        """
        item = self.items[row]
        return [db_map.codename for db_map in item.db_maps]


class EditEntityClassesDialog(ShowIconColorEditorMixin, EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for updating entity classes."""

    def __init__(self, parent, db_mngr, selected):
        """Init class.

        Args:
            parent (SpineDBEditor): data store widget
            db_mngr (SpineDBManager): the manager to do the update
            selected (set): set of EntityClassItem instances to edit
        """
        super().__init__(parent, db_mngr)
        self.setWindowTitle("Edit entity classes")
        self.table_view.set_column_converter_for_pasting("display icon", string_to_display_icon)
        self.table_view.set_column_converter_for_pasting("active by default", string_to_bool)
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageEntityClassesDelegate(self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(
            ["entity class name", "description", "display icon", "active by default", "databases"]
        )
        self.orig_data = list()
        self.default_display_icon = default_icon_id()
        model_data = list()
        for item in selected:
            data = item.db_map_data(item.first_db_map)
            row_data = [item.name, data["description"], data["display_icon"], data["active_by_default"]]
            self.orig_data.append(row_data.copy())
            row_data.append(item.display_database)
            model_data.append(row_data)
            self.items.append(item)
        self.model.reset_model(model_data)

    def connect_signals(self):
        super().connect_signals()
        # pylint: disable=unnecessary-lambda
        self.table_view.itemDelegate().icon_color_editor_requested.connect(
            lambda index: self.show_icon_color_editor(index)
        )

    @Slot()
    def accept(self):
        """Collect info from dialog and try to update items."""
        db_map_data = dict()
        for i in range(self.model.rowCount()):
            name, description, display_icon, active_by_default, db_names = self.model.row_data(i)
            if db_names is None:
                db_names = ""
            item = self.items[i]
            db_maps = []
            for database in db_names.split(","):
                db_map = next((db_map for db_map in item.db_maps if db_map.codename == database), None)
                if db_map is None:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(database, i + 1))
                    return
                db_maps.append(db_map)
            if not name:
                self.parent().msg_error.emit("Entity class name missing at row {}".format(i + 1))
                return
            orig_row = self.orig_data[i]
            if [name, description] == orig_row:
                continue
            if not display_icon:
                display_icon = self.default_display_icon
            for db_map in db_maps:
                db_item = {
                    "id": item.db_map_id(db_map),
                    "name": name,
                    "description": description,
                    "display_icon": display_icon,
                    "active_by_default": active_by_default,
                }
                db_map_data.setdefault(db_map, []).append(db_item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to update")
            return
        self.db_mngr.update_entity_classes(db_map_data)
        super().accept()


class EditEntitiesDialog(GetEntityClassesMixin, GetEntitiesMixin, EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for updating entities."""

    def __init__(self, parent, db_mngr, selected, class_key):
        """Init class.

        Args:
            parent (SpineDBEditor): data store widget
            db_mngr (SpineDBManager): the manager to do the update
            selected (set): set of EntityItem instances to edit
            class_key (tuple): for identifying the entity class
        """
        super().__init__(parent, db_mngr)
        self.setWindowTitle("Edit entities")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageEntitiesDelegate(self))
        self.connect_signals()
        self.db_maps = set(db_map for item in selected for db_map in item.db_maps)
        self.keyed_db_maps = {x.codename: x for x in self.db_maps}
        self.class_key = class_key
        self.model.set_horizontal_header_labels(
            [x + " byname" for x in self.dimension_name_list] + ["entity name", "databases"]
        )
        self.orig_data = []
        model_data = []
        for item in selected:
            data = item.db_map_data(item.first_db_map)
            row_data = [DB_ITEM_SEPARATOR.join(byname) for byname in item.element_byname_list] + [data["name"]]
            self.orig_data.append(row_data.copy())
            row_data.append(item.display_database)
            model_data.append(row_data)
            self.items.append(item)
        self.model.reset_model(model_data)

    @Slot()
    def accept(self):
        """Collect info from dialog and try to update items."""
        db_map_data = dict()
        name_column = self.model.horizontal_header_labels().index("entity name")
        db_column = self.model.horizontal_header_labels().index("databases")
        for i in range(self.model.rowCount()):
            row_data = self.model.row_data(i)
            item = self.items[i]
            element_name_list = [row_data[column] for column in range(name_column)]
            name = row_data[name_column]
            if not name:
                self.parent().msg_error.emit("Entity name missing at row {}".format(i + 1))
                return
            orig_row = self.orig_data[i]
            if [*element_name_list, name] == orig_row:
                continue
            db_names = row_data[db_column]
            if db_names is None:
                db_names = ""
            db_maps = []
            for database in db_names.split(","):
                db_map = next((db_map for db_map in item.db_maps if db_map.codename == database), None)
                if db_map is None:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(database, i + 1))
                    return
                db_maps.append(db_map)
            pre_db_item = {"name": name}
            for db_map in db_maps:
                id_ = item.db_map_id(db_map)
                # Find dimension_id_list
                entity_classes = self.db_map_ent_cls_lookup[db_map]
                if (self.class_key) not in entity_classes:
                    self.parent().msg_error.emit(
                        f"Invalid entity class '{self.class_name}' for db '{db_map.codename}' at row {i + 1}"
                    )
                    return
                ent_cls = entity_classes[self.class_key]
                dimension_id_list = ent_cls["dimension_id_list"]
                entities = self.db_map_ent_lookup[db_map]
                # Find element_id_list
                element_id_list = list()
                for dimension_id, element_name in zip(dimension_id_list, element_name_list):
                    if (dimension_id, element_name) not in entities:
                        self.parent().msg_error.emit(
                            f"Invalid entity '{element_name}' for db '{db_map.codename}' at row {i + 1}"
                        )
                        return
                    element_id = entities[dimension_id, element_name]["id"]
                    element_id_list.append(element_id)
                db_item = pre_db_item.copy()
                db_item.update({"id": id_, "element_id_list": element_id_list})
                db_map_data.setdefault(db_map, []).append(db_item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to update")
            return
        self.db_mngr.update_entities(db_map_data)
        super().accept()


class RemoveEntitiesDialog(EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for removing tree items."""

    def __init__(self, parent, db_mngr, selected):
        """
        Args:
            parent (SpineDBEditor): data store widget
            db_mngr (SpineDBManager): the manager to do the removal
            selected (dict): maps item type (class) to instances
        """
        super().__init__(parent, db_mngr)
        self.setWindowTitle("Remove items")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(RemoveEntitiesDelegate(self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(["type", "name", "databases"])
        model_data = list()
        for item_type, items in selected.items():
            for item in items:
                row_data = [item_type, item.name, item.display_database]
                model_data.append(row_data)
                self.items.append(item)
        self.model.reset_model(model_data)

    @Slot()
    def accept(self):
        """Collect info from dialog and try to remove items."""
        db_map_typed_data = dict()
        for i in range(self.model.rowCount()):
            item_type, _, db_names = self.model.row_data(i)
            if db_names is None:
                db_names = ""
            item = self.items[i]
            db_maps = []
            for database in db_names.split(","):
                db_map = next((db_map for db_map in item.db_maps if db_map.codename == database), None)
                if db_map is None:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(database, i + 1))
                    return
                db_maps.append(db_map)
            for db_map in db_maps:
                id_ = item.db_map_id(db_map)
                db_map_typed_data.setdefault(db_map, {}).setdefault(item_type, set()).add(id_)
        if not any(db_map_typed_data.values()):
            self.parent().msg_error.emit("Nothing to remove")
            return
        self.db_mngr.remove_items(db_map_typed_data)
        super().accept()


class SelectSuperclassDialog(GetEntityClassesMixin, DialogWithButtons):
    def __init__(self, parent, entity_class_item, db_mngr, *db_maps):
        super().__init__(parent, db_mngr)
        self.entity_class_item = entity_class_item
        self.db_maps = db_maps
        self._tab_widget = QTabWidget(self)
        self._subclass_name = self.entity_class_item.name
        self._combobox_superclass_subclass = {}
        for db_map in self.db_maps:
            combobox = QComboBox(self)
            superclass_subclass = db_map.get_item("superclass_subclass", subclass_name=self._subclass_name)
            self._combobox_superclass_subclass[db_map] = (combobox, superclass_subclass)
            entity_classes = self._entity_class_name_list_from_db_maps(db_map)
            combobox.addItems(["(None)"] + [x for x in entity_classes if x != self._subclass_name])
            if superclass_subclass:
                combobox.setCurrentText(superclass_subclass["superclass_name"])
            else:
                combobox.setCurrentIndex(0)
            self._tab_widget.addTab(combobox, db_map.codename)
        self.connect_signals()
        self.setWindowTitle(f"Select {self._subclass_name}'s superclass")

    def _populate_layout(self):
        self.layout().addWidget(self._tab_widget)
        super()._populate_layout()

    @Slot()
    def accept(self):
        db_map_data_to_add = {}
        db_map_data_to_upd = {}
        db_map_typed_ids_to_rm = {}
        for db_map, (combobox, superclass_subclass) in self._combobox_superclass_subclass.items():
            if combobox.currentIndex() == 0:
                if superclass_subclass:
                    db_map_typed_ids_to_rm[db_map] = {"superclass_subclass": {superclass_subclass["id"]}}
                continue
            superclass_name = combobox.currentText()
            if not superclass_subclass:
                db_map_data_to_add[db_map] = [
                    {"subclass_name": self._subclass_name, "superclass_name": superclass_name}
                ]
            elif superclass_name != superclass_subclass["superclass_name"]:
                db_map_data_to_upd[db_map] = [{"id": superclass_subclass["id"], "superclass_name": superclass_name}]
        if not db_map_data_to_add and not db_map_data_to_upd and not db_map_typed_ids_to_rm:
            self.parent().msg_error.emit("Nothing changed")
            return
        identifier = self.db_mngr.get_command_identifier()
        self.db_mngr.add_items("superclass_subclass", db_map_data_to_add, identifier=identifier)
        self.db_mngr.update_items("superclass_subclass", db_map_data_to_upd, identifier=identifier)
        self.db_mngr.remove_items(db_map_typed_ids_to_rm, identifier=identifier)
        super().accept()
