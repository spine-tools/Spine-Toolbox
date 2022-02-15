######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains :class:`ItemMetadataTableModel` and associated functionality.

:author: A. Soininen (VTT)
:date:   25.3.2022
"""
from PySide2.QtCore import QModelIndex

from spinetoolbox.mvcmodels.empty_row_model import EmptyRowModel


class ItemMetadataTableModel(EmptyRowModel):
    """Model for entity and parameter value metadata."""

    def __init__(self, db_mngr, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): database manager
            parent (QObject): parent object
        """
        super().__init__(parent, ["name", "value"])
        self._db_mngr = db_mngr
        self._db_map_ids = {}

    def set_entity_ids(self, db_map_ids):
        """Sets the model to show metadata from given entity.

        Args:
            db_map_ids (dict): mapping from database mapping to entity's id in that database
        """
        self._db_map_ids = db_map_ids
        metadata = {
            db_map.codename: self._db_mngr.get_metadata_per_entity(db_map, [entity_id])
            for db_map, entity_id in db_map_ids.items()
        }
        data = [
            [name, value, codename]
            for codename, entity_metadata in metadata.items()
            for item in entity_metadata.values()
            for name, value in item.items()
        ]
        self.default_row = {"database": list(metadata.keys())[-1]}
        self.reset_model(data)

    def batch_set_data(self, indexes, data):
        """See base class."""
        if not super().batch_set_data(indexes, data):
            return False
        rows = {ind.row() for ind in indexes}
        db_map_data = self._make_db_map_data(rows)
        self.add_items_to_db(db_map_data)
        return True

    def _make_metadata_db_map_data(self, rows):
        """Makes database add/update data for given rows.

        Args:
            rows (Iterable of int): rows for which to make the data

        Returns:
            list of dict: add/update data
        """
        db_map_data = []
        for row in rows:
            row_data = self._main_data[row]
            if any(element is None for element in row_data):
                continue
            db_map_data.append({row_data[0]: row_data[1]})
        return db_map_data

    def add_items_to_db(self, db_map_data):
        """Adds items to db.

        Args:
            db_map_data (dict): mapping DiffDatabaseMapping instance to list of items
        """
        self.build_lookup_dictionary(db_map_data)
        db_map_param_def = dict()
        db_map_error_log = dict()
        for db_map, items in db_map_data.items():
            for item in items:
                def_item, errors = self._convert_to_db(item, db_map)
                if self._check_item(def_item):
                    db_map_param_def.setdefault(db_map, []).append(def_item)
                if errors:
                    db_map_error_log.setdefault(db_map, []).extend(errors)
        if any(db_map_param_def.values()):
            self.db_mngr.add_parameter_definitions(db_map_param_def)
        if db_map_error_log:
            self.db_mngr.error_msg.emit(db_map_error_log)

    def update_items_in_db(self, items):
        """Updates items in db.

        Args:
            items (list): dictionary-items
        """
        parameter_values = list()
        error_log = list()
        db_map_data = dict()
        db_map_data[self.db_map] = items
        self.build_lookup_dictionary(db_map_data)
        for item in items:
            param_val, errors = self._convert_to_db(item, self.db_map)
            if tuple(param_val.keys()) != ("id",):
                parameter_values.append(param_val)
            if errors:
                error_log += errors
        if parameter_values:
            self.db_mngr.update_parameter_values({self.db_map: parameter_values})
        if error_log:
            self.db_mngr.error_msg.emit({self.db_map: error_log})
