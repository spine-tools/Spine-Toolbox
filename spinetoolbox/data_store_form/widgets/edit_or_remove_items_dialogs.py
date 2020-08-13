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
Classes for custom QDialogs to edit items in databases.

:author: M. Marin (KTH)
:date:   13.5.2018
"""

from PySide2.QtCore import Slot
from ...mvcmodels.minimal_table_model import MinimalTableModel
from ...widgets.custom_delegates import CheckBoxDelegate
from .custom_delegates import (
    ManageObjectClassesDelegate,
    ManageObjectsDelegate,
    ManageRelationshipClassesDelegate,
    ManageRelationshipsDelegate,
    RemoveEntitiesDelegate,
)
from .manage_items_dialogs import (
    ShowIconColorEditorMixin,
    GetObjectsMixin,
    GetRelationshipClassesMixin,
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


class EditObjectClassesDialog(ShowIconColorEditorMixin, EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for updating object classes."""

    def __init__(self, parent, db_mngr, selected):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            db_mngr (SpineDBManager): the manager to do the update
            selected (set): set of ObjectClassItem instances to edit
        """
        super().__init__(parent, db_mngr)
        self.setWindowTitle("Edit object classes")
        self.model = MinimalTableModel(self)
        self.model.set_horizontal_header_labels(['object_class name', 'description', 'display icon', 'databases'])
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageObjectClassesDelegate(self))
        self.connect_signals()
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

    def all_db_maps(self, row):
        """Returns a list of db maps available for a given row.
        Used by ShowIconColorEditorMixin.
        """
        item = self.items[row]
        return item.db_maps

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
                for db_map in item.db_maps:
                    if db_map.codename == database:
                        db_maps.append(db_map)
                        break
                else:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(database, i + 1))
                    return
            if not name:
                self.parent().msg_error.emit("Object class name missing at row {}".format(i + 1))
                return
            orig_row = self.orig_data[i]
            if [name, description, display_icon] == orig_row:
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
        self.db_mngr.update_object_classes(db_map_data)
        super().accept()


class EditObjectsDialog(EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for updating objects.
    """

    def __init__(self, parent, db_mngr, selected):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            db_mngr (SpineDBManager): the manager to do the update
            selected (set): set of ObjectItem instances to edit
        """
        super().__init__(parent, db_mngr)
        self.setWindowTitle("Edit objects")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageObjectsDelegate(self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['object name', 'description', 'databases'])
        self.orig_data = list()
        model_data = list()
        for item in selected:
            data = item.db_map_data(item.first_db_map)
            row_data = [item.display_data, data['description']]
            self.orig_data.append(row_data.copy())
            row_data.append(item.display_database)
            model_data.append(row_data)
            self.items.append(item)
        self.model.reset_model(model_data)

    @Slot()
    def accept(self):
        """Collect info from dialog and try to update items."""
        db_map_data = dict()
        for i in range(self.model.rowCount()):
            name, description, db_names = self.model.row_data(i)
            if db_names is None:
                db_names = ""
            item = self.items[i]
            db_maps = []
            for database in db_names.split(","):
                for db_map in item.db_maps:
                    if db_map.codename == database:
                        db_maps.append(db_map)
                        break
                else:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(database, i + 1))
                    return
            if not name:
                self.parent().msg_error.emit("Object name missing at row {}".format(i + 1))
                return
            orig_row = self.orig_data[i]
            if [name, description] == orig_row:
                continue
            pre_db_item = {'name': name, 'description': description}
            for db_map in db_maps:
                db_item = pre_db_item.copy()
                db_item['id'] = item.db_map_id(db_map)
                db_map_data.setdefault(db_map, []).append(db_item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to update")
            return
        self.db_mngr.update_objects(db_map_data)
        super().accept()


class EditRelationshipClassesDialog(EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for updating relationship classes.
    """

    def __init__(self, parent, db_mngr, selected):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            db_mngr (SpineDBManager): the manager to do the update
            selected (set): set of RelationshipClassItem instances to edit
        """
        super().__init__(parent, db_mngr)
        self.setWindowTitle("Edit relationship classes")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageRelationshipClassesDelegate(self))
        self.connect_signals()
        self.model.set_horizontal_header_labels(['relationship_class name', 'description', 'databases'])
        self.orig_data = list()
        model_data = list()
        for item in selected:
            data = item.db_map_data(item.first_db_map)
            row_data = [item.display_data, data['description']]
            self.orig_data.append(row_data.copy())
            row_data.append(item.display_database)
            model_data.append(row_data)
            self.items.append(item)
        self.model.reset_model(model_data)

    @Slot()
    def accept(self):
        """Collect info from dialog and try to update items."""
        db_map_data = dict()
        for i in range(self.model.rowCount()):
            name, description, db_names = self.model.row_data(i)
            if db_names is None:
                db_names = ""
            item = self.items[i]
            db_maps = []
            for database in db_names.split(","):
                for db_map in item.db_maps:
                    if db_map.codename == database:
                        db_maps.append(db_map)
                        break
                else:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(database, i + 1))
                    return
            if not name:
                self.parent().msg_error.emit("Relationship class name missing at row {}".format(i + 1))
                return
            orig_row = self.orig_data[i]
            if [name, description] == orig_row:
                continue
            pre_db_item = {'name': name, 'description': description}
            for db_map in db_maps:
                db_item = pre_db_item.copy()
                db_item['id'] = item.db_map_id(db_map)
                db_map_data.setdefault(db_map, []).append(db_item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to update")
            return
        self.db_mngr.update_relationship_classes(db_map_data)
        super().accept()


class EditRelationshipsDialog(GetRelationshipClassesMixin, GetObjectsMixin, EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for updating relationships.
    """

    def __init__(self, parent, db_mngr, selected, class_key):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            db_mngr (SpineDBManager): the manager to do the update
            selected (set): set of RelationshipItem instances to edit
            class_key (tuple): (class_name, object_class_name_list) for identifying the relationship_class
        """
        super().__init__(parent, db_mngr)
        self.setWindowTitle("Edit relationships")
        self.model = MinimalTableModel(self)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageRelationshipsDelegate(self))
        self.connect_signals()
        self.class_name, self.object_class_name_list = class_key
        object_class_name_list = self.object_class_name_list.split(",")
        self.model.set_horizontal_header_labels(
            [x + ' name' for x in object_class_name_list] + ['relationship name', 'databases']
        )
        self.orig_data = list()
        model_data = list()
        self.db_maps = set()
        for item in selected:
            self.db_maps.update(item.db_maps)
            object_name_list = item.object_name_list.split(",")
            data = item.db_map_data(item.first_db_map)
            row_data = [*object_name_list, data["name"]]
            self.orig_data.append(row_data.copy())
            row_data.append(item.display_database)
            model_data.append(row_data)
            self.items.append(item)
        self.model.reset_model(model_data)
        self.keyed_db_maps = {x.codename: x for x in self.db_maps}
        self.db_map_obj_lookup = self.make_db_map_obj_lookup()
        self.db_map_rel_cls_lookup = self.make_db_map_rel_cls_lookup()

    @Slot()
    def accept(self):
        """Collect info from dialog and try to update items."""
        db_map_data = dict()
        name_column = self.model.horizontal_header_labels().index("relationship name")
        db_column = self.model.horizontal_header_labels().index("databases")
        for i in range(self.model.rowCount()):
            row_data = self.model.row_data(i)
            item = self.items[i]
            object_name_list = [row_data[column] for column in range(name_column)]
            name = row_data[name_column]
            db_names = row_data[db_column]
            if db_names is None:
                db_names = ""
            db_maps = []
            for database in db_names.split(","):
                for db_map in item.db_maps:
                    if db_map.codename == database:
                        db_maps.append(db_map)
                        break
                else:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(database, i + 1))
                    return
            if not name:
                self.parent().msg_error.emit("Relationship class name missing at row {}".format(i + 1))
                return
            orig_row = self.orig_data[i]
            if [*object_name_list, name] == orig_row:
                continue
            pre_db_item = {'name': name}
            for db_map in db_maps:
                id_ = item.db_map_id(db_map)
                # Find object_class_id_list
                relationship_classes = self.db_map_rel_cls_lookup[db_map]
                if (self.class_name, self.object_class_name_list) not in relationship_classes:
                    self.parent().msg_error.emit(
                        "Invalid relationship_class '{}' for db '{}' at row {}".format(
                            self.class_name, db_map.codename, i + 1
                        )
                    )
                    return
                rel_cls = relationship_classes[self.class_name, self.object_class_name_list]
                object_class_id_list = rel_cls["object_class_id_list"]
                object_class_id_list = [int(x) for x in object_class_id_list.split(",")]
                objects = self.db_map_obj_lookup[db_map]
                # Find object_id_list
                object_id_list = list()
                for object_class_id, object_name in zip(object_class_id_list, object_name_list):
                    if (object_class_id, object_name) not in objects:
                        self.parent().msg_error.emit(
                            "Invalid object '{}' for db '{}' at row {}".format(object_name, db_map.codename, i + 1)
                        )
                        return
                    object_id = objects[object_class_id, object_name]["id"]
                    object_id_list.append(object_id)
                db_item = pre_db_item.copy()
                db_item.update({'id': id_, 'object_id_list': object_id_list, 'name': name})
                db_map_data.setdefault(db_map, []).append(db_item)
        if not db_map_data:
            self.parent().msg_error.emit("Nothing to update")
            return
        self.db_mngr.update_relationships(db_map_data)
        super().accept()


class RemoveEntitiesDialog(EditOrRemoveItemsDialog):
    """A dialog to query user's preferences for removing tree items.
    """

    def __init__(self, parent, db_mngr, selected):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
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
                for db_map in item.db_maps:
                    if db_map.codename == database:
                        db_maps.append(db_map)
                        break
                else:
                    self.parent().msg_error.emit("Invalid database {0} at row {1}".format(database, i + 1))
                    return
            for db_map in db_maps:
                id_ = item.db_map_id(db_map)
                db_map_typed_data.setdefault(db_map, {}).setdefault(item_type, set()).add(id_)
        if not any(db_map_typed_data.values()):
            self.parent().msg_error.emit("Nothing to remove")
            return
        self.db_mngr.remove_items(db_map_typed_data)
        super().accept()
