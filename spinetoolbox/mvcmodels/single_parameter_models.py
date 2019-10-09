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
Single models for parameter definitions and values (as 'for a single entity').

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from ..mvcmodels.filled_parameter_models import (
    FilledObjectParameterDefinitionModel,
    FilledRelationshipParameterDefinitionModel,
    FilledObjectParameterValueModel,
    FilledRelationshipParameterValueModel,
)
from ..mvcmodels.parameter_item import (
    ObjectParameterDefinitionItem,
    ObjectParameterValueItem,
    RelationshipParameterDefinitionItem,
    RelationshipParameterValueItem,
)


class SingleParameterMixin:
    """Provides an interface to associate a parameter model with a single entity class
    and do some filtering on the rows.
    """

    def __init__(self, parent, database, *args, **kwargs):
        """Init class.

        Args:
            database (str): the database where the entity class associated with this model lives.
        """
        super().__init__(parent, *args, **kwargs)
        self.database = database
        self.db_map = parent.db_name_to_map[database]
        self._auto_filter = dict()
        self._selected_param_def_ids = set()

    @property
    def entity_class_id(self):
        """Returns the associated entity class id."""
        raise NotImplementedError()

    def filter_accepts_row(self, row, ignored_columns=None):
        return self._main_filter_accepts_row(row) and self._auto_filter_accepts_row(
            row, ignored_columns=ignored_columns
        )

    def _main_filter_accepts_row(self, row):
        """Applies the main filter, defined by the selections in the grand parent."""
        if self._selected_param_def_ids:
            parameter_definition_id = self._main_data[row].parameter_definition_id
            return parameter_definition_id in self._selected_param_def_ids
        return True

    def _auto_filter_accepts_row(self, row, ignored_columns=None):
        """Aplies the autofilter, defined by the autofilter drop down menu."""
        if ignored_columns is None:
            ignored_columns = []
        for column, values in self._auto_filter.items():
            if column in ignored_columns:
                continue
            if self._main_data[row][column] in values:
                return False
        return True

    def accepted_rows(self, ignored_columns=None):
        """Returns a list of accepted rows, for convenience."""
        return [row for row in range(self.rowCount()) if self.filter_accepts_row(row, ignored_columns=ignored_columns)]


class SingleObjectParameterMixin(SingleParameterMixin):
    """Associates a parameter model with a single object class."""

    def __init__(self, parent, database, object_class_id, *args, **kwargs):
        """Init class.

        Args:
            parent (CompoundParameterModel): the parent model
            database (str): the database where the object class associated with this model lives.
            object_class_id (int): the id of the object class
        """
        super().__init__(parent, database, *args, **kwargs)
        self.object_class_id = object_class_id

    @property
    def entity_class_id(self):
        return self.object_class_id


class SingleRelationshipParameterMixin(SingleParameterMixin):
    """Associates a parameter model with a single relationship class."""

    def __init__(self, parent, database, relationship_class_id, object_class_id_list, *args, **kwargs):
        """Init class.

        Args:
            parent (CompoundParameterModel): the parent model
            database (str): the database where the relationship class associated with this model lives.
            relationship_class_id (int): the id of the relationship class
            object_class_id_list (str): comma separated string of member object class ids
        """
        super().__init__(parent, database, *args, **kwargs)
        self.relationship_class_id = relationship_class_id
        self.object_class_id_list = [int(id_) for id_ in object_class_id_list.split(",")]

    @property
    def entity_class_id(self):
        return self.relationship_class_id


class SingleObjectParameterValueMixin(SingleParameterMixin):
    """Filters objects in a parameter value model."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_object_ids = {}

    def _main_filter_accepts_row(self, row):
        """Reimplemented to filter objects."""
        if not super()._main_filter_accepts_row(row):
            return False
        if self._selected_object_ids:
            object_id = self._main_data[row].object_id
            return object_id in self._selected_object_ids
        return True


class SingleRelationshipParameterValueMixin(SingleParameterMixin):
    """Filters relationships in a parameter value model."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_object_ids = {}
        self._selected_object_id_lists = {}

    def _main_filter_accepts_row(self, row):
        """Reimplemented to filter relationships and objects."""
        if not super()._main_filter_accepts_row(row):
            return False
        object_id_list = self._main_data[row].object_id_list
        if self._selected_object_id_lists:
            return object_id_list in self._selected_object_id_lists
        if self._selected_object_ids:
            return bool(self._selected_object_ids.intersection(int(x) for x in object_id_list.split(",")))
        return True


class SingleObjectParameterDefinitionModel(SingleObjectParameterMixin, FilledObjectParameterDefinitionModel):
    """An object parameter definition model for a single object class."""

    def fetch_data(self):
        sq = self.db_map.object_parameter_definition_sq
        return [
            ObjectParameterDefinitionItem(self.header, database=self.database, **param_def._asdict())
            for param_def in self.db_map.query(sq).filter_by(object_class_id=self.object_class_id)
        ]


class SingleRelationshipParameterDefinitionModel(
    SingleRelationshipParameterMixin, FilledRelationshipParameterDefinitionModel
):
    """A relationship parameter definition model for a single relationship class."""

    def fetch_data(self):
        sq = self.db_map.relationship_parameter_definition_sq
        return [
            RelationshipParameterDefinitionItem(self.header, database=self.database, **param_def._asdict())
            for param_def in self.db_map.query(sq).filter_by(relationship_class_id=self.relationship_class_id)
        ]


class SingleObjectParameterValueModel(
    SingleObjectParameterMixin, SingleObjectParameterValueMixin, FilledObjectParameterValueModel
):
    """An object parameter value model for a single object class."""

    def fetch_data(self):
        sq = self.db_map.object_parameter_value_sq
        return [
            ObjectParameterValueItem(self.header, database=self.database, **param_val._asdict())
            for param_val in self.db_map.query(sq).filter_by(object_class_id=self.object_class_id)
        ]


class SingleRelationshipParameterValueModel(
    SingleRelationshipParameterMixin, SingleRelationshipParameterValueMixin, FilledRelationshipParameterValueModel
):
    """A relationship parameter value model for a single relationship class."""

    def fetch_data(self):
        sq = self.db_map.relationship_parameter_value_sq
        return [
            RelationshipParameterValueItem(self.header, database=self.database, **param_val._asdict())
            for param_val in self.db_map.query(sq).filter_by(relationship_class_id=self.relationship_class_id)
        ]
