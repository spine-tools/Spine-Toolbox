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
Models for parameter definitions and values corresponding to a single class.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QGuiApplication
from helpers import busy_effect
from mvcmodels.minimal_table_model import MinimalTableModel
from mvcmodels.parameter_mixins import BaseParameterMixin, ParameterDefinitionMixin
from mvcmodels.parameter_value_formatting import format_for_DisplayRole, format_for_ToolTipRole


class SubParameterModel(BaseParameterMixin, MinimalTableModel):
    """A parameter model for a single entity class."""

    # TODO: how column insertion/removal impacts fixed_columns?

    def __init__(self, parent, item_updater_attr, json_fields=()):
        """Initialize class.

        Args:
            parent (ParameterModel): the parent object
            item_maker (function): a function to create items to put in the model rows
            item_injector_attr (str): the name of the method in DiffDatabaseMapping to add items to the db
        """
        super().__init__(parent)
        self.db_name_to_map = parent.db_name_to_map
        self._item_updater_attr = item_updater_attr
        self._json_fields = json_fields
        self._gray_brush = QGuiApplication.palette().button()
        self.error_log = []
        self.updated_count = 0

    def flags(self, index):
        """Make fixed indexes non-editable."""
        flags = super().flags(index)
        if index.column() in self._parent.fixed_columns:
            return flags & ~Qt.ItemIsEditable
        return flags

    def data(self, index, role=Qt.DisplayRole):
        """Paint background of fixed indexes gray and apply custom format to JSON fields."""
        column = index.column()
        if column in self._parent.fixed_columns and role == Qt.BackgroundRole:
            return self._gray_brush
        if self._parent.header[column] in self._json_fields:
            if role == Qt.ToolTipRole:
                return format_for_ToolTipRole(super().data(index, Qt.EditRole))
            if role == Qt.DisplayRole:
                return format_for_DisplayRole(super().data(index, Qt.EditRole))
        return super().data(index, role)

    def batch_set_data(self, indexes, data):
        """Sets data for indexes in batch.
        Set data in model first, then set internal data for modified items.
        Finally update successfully modified items in the db.
        """
        self.error_log.clear()
        self.updated_count = 0
        if not super().batch_set_data(indexes, data):
            return False
        rows = {ind.row(): self._main_data[ind.row()] for ind in indexes}
        self.batch_autocomplete_data(rows)
        self.update_items_in_db(rows)
        return True

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
            item_updater = db_map.__getattribute__(self._item_updater_attr)
            upd_items, error_log = item_updater(item_for_update)
            if error_log:
                self.error_log.extend(error_log)
                item.revert()
                # TODO: emit dataChanged when revert
            item.clear_cache()
            self.updated_count += 1


class SubParameterDefinitionModel(ParameterDefinitionMixin, SubParameterModel):
    """A parameter definition model for a single entity class.
    """

    def __init__(self, parent):
        super().__init__(parent, item_updater_attr="update_parameter_definitions", json_fields=("default_value"))

    def update_items_in_db(self, rows):
        """Updates items in database.
        Call the super method to update parameter definitions, then the method to set tags.

        Args:
            rows (dict): A dict mapping row numbers to items that should be updated in the db
        """
        super().update_items_in_db(rows)
        self.set_parameter_definition_tags_in_db(rows)


class SubParameterValueModel(SubParameterModel):
    """A parameter value model for a single entity class.
    """

    def __init__(self, parent):
        super().__init__(parent, item_updater_attr="update_parameter_values", json_fields=("value"))
