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

from ..mvcmodels.filled_parameter_models import FilledParameterDefinitionModel, FilledParameterValueModel
from ..mvcmodels.parameter_mixins import (
    SingleObjectParameterMixin,
    SingleRelationshipParameterMixin,
    ObjectParameterDecorateMixin,
    RelationshipParameterDecorateMixin,
)
from ..mvcmodels.parameter_item import (
    ObjectParameterDefinitionItem,
    ObjectParameterValueItem,
    RelationshipParameterDefinitionItem,
    RelationshipParameterValueItem,
)


class SingleObjectParameterDefinitionModel(
    ObjectParameterDecorateMixin, SingleObjectParameterMixin, FilledParameterDefinitionModel
):
    """An object parameter definition model for a single object class."""

    def get_data_from_db(self):
        sq = self.db_map.object_parameter_definition_sq
        return [
            ObjectParameterDefinitionItem(self.header, database=self.database, **param_def._asdict())
            for param_def in self.db_map.query(sq).filter_by(object_class_id=self.object_class_id)
        ]


class SingleRelationshipParameterDefinitionModel(
    RelationshipParameterDecorateMixin, SingleRelationshipParameterMixin, FilledParameterDefinitionModel
):
    """A relationship parameter definition model for a single relationship class."""

    def get_data_from_db(self):
        sq = self.db_map.relationship_parameter_definition_sq
        return [
            RelationshipParameterDefinitionItem(self.header, database=self.database, **param_def._asdict())
            for param_def in self.db_map.query(sq).filter_by(relationship_class_id=self.relationship_class_id)
        ]


class SingleObjectParameterValueModel(
    ObjectParameterDecorateMixin, SingleObjectParameterMixin, FilledParameterValueModel
):
    """An object parameter value model for a single object class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_object_ids = {}

    def get_data_from_db(self):
        sq = self.db_map.object_parameter_value_sq
        return [
            ObjectParameterValueItem(self.header, database=self.database, **param_val._asdict())
            for param_val in self.db_map.query(sq).filter_by(object_class_id=self.object_class_id)
        ]

    def _main_filter_accepts_row(self, row):
        """Reimplemented to filter objects."""
        if not super()._main_filter_accepts_row(row):
            return False
        if self._selected_object_ids:
            object_id = self._main_data[row].object_id
            return object_id in self._selected_object_ids
        return True


class SingleRelationshipParameterValueModel(
    RelationshipParameterDecorateMixin, SingleRelationshipParameterMixin, FilledParameterValueModel
):
    """A relationship parameter value model for a single relationship class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_object_ids = {}
        self._selected_object_id_lists = {}

    def get_data_from_db(self):
        sq = self.db_map.relationship_parameter_value_sq
        return [
            RelationshipParameterValueItem(self.header, database=self.database, **param_val._asdict())
            for param_val in self.db_map.query(sq).filter_by(relationship_class_id=self.relationship_class_id)
        ]

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
