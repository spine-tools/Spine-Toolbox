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
Classes for custom QDialogs to edit items in databases.
"""

from PySide6.QtCore import Slot
from ...mvcmodels.minimal_table_model import MinimalTableModel
from .custom_delegates import ManageEntityClassesDelegate, ManageEntitiesDelegate, RemoveEntitiesDelegate
from .manage_items_dialogs import (
    ShowIconColorEditorMixin,
    GetEntitiesMixin,
    GetEntityClassesMixin,
    ManageItemsDialog,
)
from ...helpers import default_icon_id


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
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageEntityClassesDelegate(self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['entity class name', 'description', 'display icon', 'databases'])
        self.orig_data = list()
        self.default_display_icon = default_icon_id()
        model_data = list()
        for item in selected:
            data = item.db_map_data(item.first_db_map)
            row_data = [item.display_data, data['description'], data['display_icon']]
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
            name, description, display_icon, db_names = self.model.row_data(i)
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
            pre_db_item = {'name': name, 'description': description, 'display_icon': display_icon}
            for db_map in db_maps:
                db_item = pre_db_item.copy()
                db_item['id'] = item.db_map_id(db_map)
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
            class_key (tuple): (class_name, dimension_name_list) for identifying the entity class
        """
        super().__init__(parent, db_mngr)
        self.setWindowTitle("Edit entities")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageEntitiesDelegate(self))
        self.connect_signals()
        self.class_name, self.dimension_name_list = class_key
        self.model.set_horizontal_header_labels(
            [x + ' name' for x in self.dimension_name_list]
            + ['entity name', 'active alternatives', 'inactive alternatives', 'databases']
        )
        self.orig_data = list()
        model_data = list()
        self.db_maps = set()
        for item in selected:
            self.db_maps.update(item.db_maps)
            data = item.db_map_data(item.first_db_map)
            row_data = [
                *item.element_name_list,
                data["name"],
                ",".join(data["active_alternative_name_list"]),
                ",".join(data["inactive_alternative_name_list"]),
            ]
            self.orig_data.append(row_data.copy())
            row_data.append(item.display_database)
            model_data.append(row_data)
            self.items.append(item)
        self.model.reset_model(model_data)
        self.keyed_db_maps = {x.codename: x for x in self.db_maps}
        self.db_map_ent_lookup = self.make_db_map_ent_lookup()
        self.db_map_ent_cls_lookup = self.make_db_map_ent_cls_lookup()
        self.db_map_alt_id_lookup = self.make_db_map_alt_id_lookup()

    @Slot()
    def accept(self):
        """Collect info from dialog and try to update items."""
        db_map_data = dict()
        name_column = self.model.horizontal_header_labels().index("entity name")
        active_column = self.model.horizontal_header_labels().index("active alternatives")
        inactive_column = self.model.horizontal_header_labels().index("inactive alternatives")
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
            active_alts = [x for x in row_data[active_column].split(",") if x]
            inactive_alts = [x for x in row_data[inactive_column].split(",") if x]
            conflicting = set(active_alts) & set(inactive_alts)
            if conflicting:
                self.parent().msg_error.emit(f"Conflicting alternatives {conflicting} at row {i + 1}")
                return
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
            pre_db_item = {'name': name}
            for db_map in db_maps:
                id_ = item.db_map_id(db_map)
                # Find dimension_id_list
                entity_classes = self.db_map_ent_cls_lookup[db_map]
                if (self.class_name, self.dimension_name_list) not in entity_classes:
                    self.parent().msg_error.emit(
                        f"Invalid entity class '{self.class_name}' for db '{db_map.codename}' at row {i + 1}"
                    )
                    return
                ent_cls = entity_classes[self.class_name, self.dimension_name_list]
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
                # Find alt id lists
                active_alt_ids = []
                inactive_alt_ids = []
                alternative_ids = self.db_map_alt_id_lookup[db_map]
                for alt_name in active_alts:
                    if alt_name not in alternative_ids:
                        self.parent().msg_error.emit(
                            f"Invalid alternative '{alt_name}' for db '{db_map.codename}' at row {i + 1}"
                        )
                        return
                    active_alt_ids.append(alternative_ids[alt_name])
                for alt_name in inactive_alts:
                    if alt_name not in alternative_ids:
                        self.parent().msg_error.emit(
                            f"Invalid alternative '{alt_name}' for db '{db_map.codename}' at row {i + 1}"
                        )
                        return
                    inactive_alt_ids.append(alternative_ids[alt_name])
                db_item = pre_db_item.copy()
                db_item.update(
                    {
                        'id': id_,
                        'element_id_list': element_id_list,
                        'active_alternative_id_list': active_alt_ids,
                        'inactive_alternative_id_list': inactive_alt_ids,
                    }
                )
                db_map_data.setdefault(db_map, []).append(db_item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to update")
            return
        self.db_mngr.update_entities(db_map_data)
        super().accept()


class RemoveEntitiesDialog(EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for removing tree items."""

    def __init__(self, parent, db_mngr, selected):
        """Init class.

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
        self.model.set_horizontal_header_labels(['type', 'name', 'databases'])
        model_data = list()
        for item_type, items in selected.items():
            for item in items:
                row_data = [item_type, item.display_data, item.display_database]
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
