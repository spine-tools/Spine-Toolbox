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
Filled models for parameter definitions and values (as in 'filled with data').

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt, QModelIndex
from PySide2.QtGui import QGuiApplication
from ..mvcmodels.minimal_table_model import MinimalTableModel
from ..mvcmodels.parameter_autocomplete_mixins import ParameterDefinitionAutocompleteMixin
from ..mvcmodels.parameter_mixins import (
    ObjectParameterDecorateMixin,
    RelationshipParameterDecorateMixin,
    ParameterDefinitionUpdateMixin,
    ParameterValueUpdateMixin,
    ObjectParameterRenameMixin,
    RelationshipParameterRenameMixin,
    ParameterDefinitionRenameRemoveMixin,
    ParameterValueRenameMixin,
    ObjectParameterValueRenameMixin,
    RelationshipParameterValueRenameMixin,
)
from ..mvcmodels.parameter_value_formatting import format_for_DisplayRole, format_for_ToolTipRole


class FilledParameterModel(MinimalTableModel):
    """A parameter model filled with data."""

    def __init__(self, parent, header, db_maps, lazy_loading=False, fixed_fields=None, json_fields=None):
        """Initialize class.

        Args:
            parent (Object): the parent object, typically a CompoundParameterModel
            header (list): list of field names for the header
            db_maps (dict): maps database names to DiffDatabaseMapping instances
        """
        super().__init__(parent, header)
        self.db_maps = db_maps
        if fixed_fields is None:
            fixed_fields = []
        if json_fields is None:
            json_fields = []
        self.fixed_fields = fixed_fields
        self.json_fields = json_fields

    def insertRows(self, row, count, parent=QModelIndex()):
        """This model doesn't support row insertion."""
        return False

    def flags(self, index):
        """Make fixed indexes non-editable."""
        flags = super().flags(index)
        if self.header[index.column()] in self.fixed_fields:
            return flags & ~Qt.ItemIsEditable
        return flags

    def data(self, index, role=Qt.DisplayRole):
        """Paint background of fixed indexes gray and apply custom format to JSON fields."""
        column = index.column()
        if self.header[column] in self.fixed_fields and role == Qt.BackgroundRole:
            return QGuiApplication.palette().button()
        if self.header[column] in self.json_fields:
            if role == Qt.ToolTipRole:
                return format_for_ToolTipRole(super().data(index, Qt.EditRole))
            if role == Qt.DisplayRole:
                return format_for_DisplayRole(super().data(index, Qt.EditRole))
        return super().data(index, role)


class FilledObjectParameterDefinitionModel(
    ObjectParameterDecorateMixin,
    ParameterDefinitionUpdateMixin,
    ParameterDefinitionAutocompleteMixin,
    ObjectParameterRenameMixin,
    ParameterDefinitionRenameRemoveMixin,
    FilledParameterModel,
):
    """An object parameter definition model filled with data."""


class FilledRelationshipParameterDefinitionModel(
    RelationshipParameterDecorateMixin,
    ParameterDefinitionUpdateMixin,
    ParameterDefinitionAutocompleteMixin,
    RelationshipParameterRenameMixin,
    ParameterDefinitionRenameRemoveMixin,
    FilledParameterModel,
):
    """A relationship parameter definition model filled with data."""


class FilledObjectParameterValueModel(
    ObjectParameterDecorateMixin,
    ParameterValueUpdateMixin,
    ObjectParameterRenameMixin,
    ParameterValueRenameMixin,
    ObjectParameterValueRenameMixin,
    FilledParameterModel,
):
    """An object parameter value model filled with data."""


class FilledRelationshipParameterValueModel(
    RelationshipParameterDecorateMixin,
    ParameterValueUpdateMixin,
    RelationshipParameterRenameMixin,
    ParameterValueRenameMixin,
    RelationshipParameterValueRenameMixin,
    FilledParameterModel,
):
    """A relationship parameter value model filled with data."""
