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
Mixins for parameter definition models

:authors: M. Marin (KTH)
:date:   4.10.2019
"""
from PySide2.QtCore import Qt


class ParameterDefinitionTagSetMixin:
    """Provides a method to set parameter definition tags."""

    def set_parameter_definition_tags_in_db(self, rows):
        """Set parameter definition tags in the db.

        Args:
            rows (dict): A dict mapping row numbers to items whose tags should be set
        """
        tag_specs_dict = dict()
        for item in rows.values():
            tag_spec = item.tag_spec()
            if tag_spec:
                tag_specs_dict.setdefault(db_map, dict()).update(tag_spec)
        for db_map, tag_specs in tag_specs_dict.items():
            _, error_log = db_map.set_parameter_definition_tags(tag_specs)
            self._error_log.extend(error_log)


class ParameterInsertMixin:
    """Handles adding parameters to the db."""

    def __init__(self, parent, *args, **kwargs):
        """Initialize class.

        Args:
            parent (Object): the parent object
        """
        super().__init__(parent, *args, **kwargs)
        self.db_name_to_map = parent.db_name_to_map
        self._error_log = []
        self._added_rows = []

    @property
    def added_rows(self):
        added_rows = self._added_rows.copy()
        self._added_rows.clear()
        return added_rows

    @property
    def error_log(self):
        error_log = self._error_log.copy()
        self._error_log.clear()
        return error_log

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch.
        If successful, add items to db.
        """
        self._error_log.clear()
        self._added_rows.clear()
        if super().batch_set_data(indexes, data):
            rows = {ind.row(): self._main_data[ind.row()] for ind in indexes}
            self.add_items_to_db(rows)
            return True
        return False

    def add_items_to_db(self, rows):
        """Adds items to database.

        Args:
            rows (dict): A dict mapping row numbers to items that should be added to the db
        """
        for row, item in rows.items():
            item = self._main_data[row]
            database = item.database
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            item_for_insert = item.for_insert()
            if not item_for_insert:
                continue
            new_items, error_log = self.do_add_items_to_db(db_map, item_for_insert)
            self.error_log.extend(error_log)
            if not error_log:
                new_item = new_items.first()
                item.id = new_item.id
                item.clear_cache()
                self._added_rows.append(row)

    @staticmethod
    def do_add_items_to_db(db_map, *items):
        """Add items to the given database.
        Reimplement in subclasses.
        """
        raise NotImplementedError()


class ParameterDefinitionInsertMixin(ParameterDefinitionTagSetMixin, ParameterInsertMixin):
    """Handles adding parameter definitions to the db."""

    @staticmethod
    def do_add_items_to_db(db_map, *items):
        """Add items to the given database."""
        return db_map.add_parameter_definitions(*items)

    def add_items_to_db(self, rows):
        """Adds items to database.
        Call the super method to add parameter definitions, then the method to set tags.

        Args:
            rows (dict): A dict mapping row numbers to items that should be added to the db
        """
        super().add_items_to_db(rows)
        self.set_parameter_definition_tags_in_db(rows)


class ParameterValueInsertMixing(ParameterInsertMixin):
    """Handles adding parameter values to the db."""

    @staticmethod
    def do_add_items_to_db(db_map, *items):
        """Add items to the given database."""
        return db_map.add_parameter_values(*items)


class ParameterUpdateMixin:
    """Handles updating parameters in the db."""

    def __init__(self, parent, *args, **kwargs):
        """Initialize class.

        Args:
            parent (ParameterModel): the parent object
        """
        super().__init__(parent, *args, **kwargs)
        self.db_name_to_map = parent.db_name_to_map
        self._error_log = []
        self._updated_count = 0

    @property
    def updated_count(self):
        updated_count = self._updated_count
        self._updated_count = 0
        return updated_count

    @property
    def error_log(self):
        error_log = self._error_log.copy()
        self._error_log.clear()
        return error_log

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch.
        Set data in model first, then set internal data for modified items.
        Finally update successfully modified items in the db.
        """
        self._error_log.clear()
        self._updated_count = 0
        if super().batch_set_data(indexes, data):
            rows = {ind.row(): self._main_data[ind.row()] for ind in indexes}
            self.update_items_in_db(rows)
            return True
        return False

    def update_items_in_db(self, rows):
        """Updates items in database.

        Args:
            rows (dict): A dict mapping row numbers to items that should be updated in the db
        """
        for row, item in rows.items():
            database = item.database
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            item_for_update = item.for_update()
            if not item_for_update:
                continue
            upd_items, error_log = self.do_update_items_in_db(db_map, item_for_update)
            if error_log:
                self._error_log.extend(error_log)
                item.revert()
                # TODO: emit dataChanged
            else:
                self._updated_count += 1
            item.clear_cache()

    @staticmethod
    def do_update_items_in_db(db_map, *items):
        """Update items in the given database.
        Must be reimplemented in subclasses.
        """
        raise NotImplementedError()


class ParameterDefinitionUpdateMixin(ParameterDefinitionTagSetMixin, ParameterUpdateMixin):
    """Handles updating parameter definitions in the db."""

    @staticmethod
    def do_update_items_in_db(db_map, *items):
        """Update items in the given database."""
        return db_map.update_parameter_definitions(*items)

    def update_items_in_db(self, rows):
        """Updates items in database.
        Call the super method to update parameter definitions, then the method to set tags.

        Args:
            rows (dict): A dict mapping row numbers to items that should be updated in the db
        """
        super().update_items_in_db(rows)
        self.set_parameter_definition_tags_in_db(rows)


class ParameterValueUpdateMixin(ParameterUpdateMixin):
    """Handles updating parameter values in the db."""

    @staticmethod
    def do_update_items_in_db(db_map, *items):
        """Update items in the given database."""
        return db_map.update_parameter_values(*items)


class ObjectParameterDecorateMixin:
    """Provides decoration features to all object parameter models."""

    def __init__(self, *args, icon_mngr=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon_mngr = icon_mngr

    def data(self, index, role=Qt.DisplayRole):
        """Return data for given index and role.
        Paint the object class icon next to the name.
        """
        if role == Qt.DecorationRole and self.header[index.column()] == "object_class_name":
            object_class_name = self._main_data[index.row()].object_class_name
            return self.icon_mngr.object_icon(object_class_name)
        return super().data(index, role)


class RelationshipParameterDecorateMixin:
    """Provides decoration features to all relationship parameter models."""

    def __init__(self, *args, icon_mngr=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.icon_mngr = icon_mngr

    def data(self, index, role=Qt.DisplayRole):
        """Return data for given index and role.
        Paint the relationship class icon next to the name.
        """
        if role == Qt.DecorationRole and self.header[index.column()] == "relationship_class_name":
            object_class_name_list = self._main_data[index.row()].object_class_name_list
            return self.icon_mngr.relationship_icon(object_class_name_list)
        return super().data(index, role)


class ParameterDefinitionRenameRemoveMixin:
    """Handles parameter definitions renaming and removal."""

    def rename_parameter_tags(self, parameter_tags):
        """Rename parameter tags.

        Args:
            parameter_tags (dict): maps id to new tag
        """
        for item in self._main_data:
            if not item.parameter_tag_id_list:
                continue
            split_parameter_tag_id_list = [int(id_) for id_ in item.parameter_tag_id_list.split(",")]
            matches = [(k, id_) for k, id_ in enumerate(split_parameter_tag_id_list) if id_ in parameter_tags]
            if not matches:
                continue
            split_parameter_tag_list = item.parameter_tag_list.split(",")
            for k, id_ in matches:
                new_tag = parameter_tags[id_]
                split_parameter_tag_list[k] = new_tag
            item.parameter_tag_list = ",".join(split_parameter_tag_list)

    def remove_parameter_tags(self, parameter_tag_ids):
        """Remove parameter tags from model.

        Args:
            parameter_tag_ids (set): set of ids to remove
        """
        for item in self._main_data:
            if not item.parameter_tag_id_list:
                continue
            split_parameter_tag_id_list = [int(id_) for id_ in item.parameter_tag_id_list.split(",")]
            matches = [k for k, id_ in enumerate(split_parameter_tag_id_list) if id_ in parameter_tag_ids]
            if not matches:
                continue
            split_parameter_tag_list = item.parameter_tag_list.split(",")
            for k in sorted(matches, reverse=True):
                del split_parameter_tag_list[k]
            item.parameter_tag_list = ",".join(split_parameter_tag_list)

    def rename_parameter_value_lists(self, value_lists):
        """Rename parameter value lists in model.

        Args:
            value_lists (dict): maps id to new name
        """
        for item in self._main_data:
            if item.value_list_id in value_lists:
                item.value_list_name = value_lists[item.value_list_id]

    def clear_parameter_value_lists(self, value_list_ids):
        """Clear parameter value_lists from model.

        Args:
            value_list_ids (set): set of ids to remove
        """
        for item in self._main_data:
            if item.value_list_id in value_list_ids:
                item.value_list_id = None
                item.value_list_name = None
