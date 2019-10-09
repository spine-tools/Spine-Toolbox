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
Empty models for parameter definitions and values.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from sqlalchemy.sql import and_, or_
from PySide2.QtCore import Qt, QModelIndex
from ..mvcmodels.empty_row_model import EmptyRowModel
from ..mvcmodels.parameter_autocomplete_mixins import (
    ParameterDefinitionAutocompleteMixin,
    ParameterValueAutocompleteMixin,
    ObjectParameterAutocompleteMixin,
    RelationshipParameterAutocompleteMixin,
    ObjectParameterValueAutocompleteMixin,
    RelationshipParameterValueAutocompleteMixin,
)
from ..mvcmodels.parameter_mixins import (
    ParameterDefinitionInsertMixin,
    ParameterValueInsertMixing,
    ObjectParameterDecorateMixin,
    RelationshipParameterDecorateMixin,
)
from ..mvcmodels.parameter_item import (
    ObjectParameterDefinitionItem,
    ObjectParameterValueItem,
    RelationshipParameterDefinitionItem,
    RelationshipParameterValueItem,
)


class EmptyParameterModel(EmptyRowModel):
    """An empty parameter model."""

    def create_item(self):
        """Returns an item to put in the model rows.
        Reimplement in subclasses to return something meaningful.
        """
        raise NotImplementedError()

    def insertRows(self, row, count, parent=QModelIndex()):
        """Inserts count rows into the model before the given row.
        Items in the new row will be children of the item represented
        by the parent model index.

        Args:
            row (int): Row number where new rows are inserted
            count (int): Number of inserted rows
            parent (QModelIndex): Parent index

        Returns:
            True if rows were inserted successfully, False otherwise
        """
        if row < 0 or row > self.rowCount():
            return False
        if count < 1:
            return False
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            # Create the new row using the `create_item` attribute
            new_main_row = self.create_item()
            # Notice if insert index > rowCount(), new object is inserted to end
            self._main_data.insert(row + i, new_main_row)
        self.endInsertRows()
        return True


class EmptyObjectParameterDefinitionModel(
    ObjectParameterDecorateMixin,
    ParameterDefinitionInsertMixin,
    ObjectParameterAutocompleteMixin,
    ParameterDefinitionAutocompleteMixin,
    EmptyParameterModel,
):
    """An empty object parameter definition model."""

    def create_item(self):
        """Returns an item to put in the model rows."""
        return ObjectParameterDefinitionItem(self.header)


class EmptyRelationshipParameterDefinitionModel(
    RelationshipParameterDecorateMixin,
    ParameterDefinitionInsertMixin,
    RelationshipParameterAutocompleteMixin,
    ParameterDefinitionAutocompleteMixin,
    EmptyParameterModel,
):
    """An empty relationship parameter definition model."""

    def create_item(self):
        return RelationshipParameterDefinitionItem(self.header)


class EmptyObjectParameterValueModel(
    ObjectParameterDecorateMixin,
    ParameterValueInsertMixing,
    ObjectParameterValueAutocompleteMixin,
    ObjectParameterAutocompleteMixin,
    ParameterValueAutocompleteMixin,
    EmptyParameterModel,
):
    """An empty object parameter value model."""

    def create_item(self):
        """Returns an item to put in the model rows."""
        return ObjectParameterValueItem(self.header)


class EmptyRelationshipParameterValueModel(
    RelationshipParameterDecorateMixin,
    ParameterValueInsertMixing,
    RelationshipParameterValueAutocompleteMixin,
    RelationshipParameterAutocompleteMixin,
    ParameterValueAutocompleteMixin,
    EmptyParameterModel,
):
    """An empty relationship parameter value model."""

    def create_item(self):
        """Returns an item to put in the model rows."""
        return RelationshipParameterValueItem(self.header)

    def add_items_to_db(self, rows):
        """Adds items to database. Add relationships on the fly first,
        then proceed to add parameter values by calling the super() method.

        Args:
            rows (dict): A dict mapping row numbers to items that should be added to the db
        """
        for row, item in rows.items():
            database = item.database
            db_map = self.db_name_to_map.get(database)
            if not db_map:
                continue
            relationship_for_insert = item.relationship_for_insert()
            if not relationship_for_insert:
                continue
            new_relationships, error_log = db_map.add_wide_relationships(relationship_for_insert)
            if error_log:
                self.error_log.extend(error_log)
                continue
            new_relationship = new_relationships.first()
            item.relationship_id = new_relationship.id
        # TODO: try and do this with signals and slots
        # self._parent._parent.object_tree_model.add_relationships(db_map, new_relationships)
        # self._parent._parent.relationship_tree_model.add_relationships(db_map, new_relationships)
        super().add_items_to_db(rows)
