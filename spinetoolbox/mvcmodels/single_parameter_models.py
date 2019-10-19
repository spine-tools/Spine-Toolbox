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

from ..mvcmodels.filled_parameter_models import FilledParameterModel
from ..mvcmodels.parameter_item import ParameterDefinitionItem, ParameterValueItem
from ..mvcmodels.parameter_mixins import ParameterDefinitionFillInMixin


class SingleParameterModel(FilledParameterModel):
    """Provides an interface to associate a parameter model with a single entity class
    and do some filtering on the rows.
    """

    def __init__(self, *args, **kwargs):
        """Init class.

        Args:
            parent (CompoundParameterModel): the parent object
            header (list): list of field names for the header
        """
        super().__init__(*args, **kwargs)
        self._auto_filter = dict()
        self._selected_param_def_ids = set()

    @property
    def item_type(self):
        raise NotImplementedError()

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


class SingleObjectParameterMixin:
    """Associates a parameter model with a single object class."""

    def __init__(self, parent, header, db_mngr, db_map, object_class_id, *args, **kwargs):
        """Init class.

        Args:
            object_class_id (int): the id of the object class
        """
        super().__init__(parent, header, db_mngr, db_map, *args, **kwargs)
        self.object_class_id = object_class_id

    @property
    def entity_class_id(self):
        return self.object_class_id


class SingleRelationshipParameterMixin:
    """Associates a parameter model with a single relationship class."""

    def __init__(self, parent, header, db_mngr, db_map, relationship_class_id, *args, **kwargs):
        """Init class.

        Args:
            relationship_class_id (int): the id of the relationship class
        """
        super().__init__(parent, header, db_mngr, db_map, *args, **kwargs)
        self.relationship_class_id = relationship_class_id

    @property
    def entity_class_id(self):
        return self.relationship_class_id


class SingleObjectParameterValueMixin:
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


class SingleRelationshipParameterValueMixin:
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


class SingleParameterDefinitionMixin(ParameterDefinitionFillInMixin):

    json_fields = ["default_value"]

    @property
    def item_type(self):
        return "parameter definition"

    def update_items_in_db(self, items):
        """Update items in db."""
        self.begin_modify_db({self.db_map: items})
        param_def_data = list()
        param_tag_data = list()
        for item in items:
            def_item = self._make_parameter_item(item, self.db_map)
            tag_item = self._make_param_tag_item(item, self.db_map)
            if def_item:
                param_def_data.append(def_item)
            if tag_item:
                param_tag_data.append(tag_item)
        self.db_mngr.set_parameter_definition_tags({self.db_map: param_tag_data})
        self.db_mngr.update_parameter_definitions({self.db_map: param_def_data})
        self.end_modify_db()


class SingleParameterValueModel:

    json_fields = ["value"]

    @property
    def item_type(self):
        return "parameter value"

    def update_items_in_db(self, items):
        """Update items in db."""
        self.db_mngr.update_parameter_values(db_map, items)


class SingleObjectParameterDefinitionModel(
    SingleParameterDefinitionMixin, SingleObjectParameterMixin, SingleParameterModel
):
    """An object parameter definition model for a single object class."""

    fixed_fields = ["object_class_name", "database"]

    def fetch_data(self):
        return [
            x["id"]
            for x in self.db_mngr.get_object_parameter_definitions(self.db_map, object_class_id=self.object_class_id)
        ]


class SingleRelationshipParameterDefinitionModel(
    SingleParameterDefinitionMixin, SingleRelationshipParameterMixin, SingleParameterModel
):
    """A relationship parameter definition model for a single relationship class."""

    fixed_fields = ["relationship_class_name", "object_class_name_list", "database"]

    def fetch_data(self):
        return [
            x["id"]
            for x in self.db_mngr.get_relationship_parameter_definitions(
                self.db_map, relationship_class_id=self.relationship_class_id
            )
        ]


class SingleObjectParameterValueModel(
    SingleParameterValueModel, SingleObjectParameterMixin, SingleObjectParameterValueMixin, SingleParameterModel
):
    """An object parameter value model for a single object class."""

    fixed_fields = ["object_class_name", "object_name", "parameter_name", "database"]

    def fetch_data(self):
        return [
            x["id"] for x in self.db_mngr.get_object_parameter_values(self.db_map, object_class_id=self.object_class_id)
        ]


class SingleRelationshipParameterValueModel(
    SingleParameterValueModel,
    SingleRelationshipParameterMixin,
    SingleRelationshipParameterValueMixin,
    SingleParameterModel,
):
    """A relationship parameter value model for a single relationship class."""

    fixed_fields = ["relationship_class_name", "object_name_list", "parameter_name", "database"]

    def fetch_data(self):
        return [
            x["id"]
            for x in self.db_mngr.get_relationship_parameter_values(
                self.db_map, relationship_class_id=self.relationship_class_id
            )
        ]
