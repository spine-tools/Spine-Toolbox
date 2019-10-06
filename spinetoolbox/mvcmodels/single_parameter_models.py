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

from PySide2.QtCore import QSortFilterProxyModel
from mvcmodels.filled_parameter_models import FilledParameterDefinitionModel, FilledParameterValueModel
from mvcmodels.parameter_mixins import (
    SingleObjectParameterMixin,
    SingleRelationshipParameterMixin,
    ObjectParameterDecorateMixin,
    RelationshipParameterDecorateMixin,
)
from mvcmodels.parameter_item import (
    ObjectParameterDefinitionItem,
    ObjectParameterValueItem,
    RelationshipParameterDefinitionItem,
    RelationshipParameterValueItem,
)


class SingleParameterModel(QSortFilterProxyModel):
    """A parameter model for a single entity class"""

    def __init__(self, parent, database):
        """Init class.

        Args:
            parent (CompoundParameterModel): the parent model
            database (str): the database where the entity class associated with this model lives.
        """
        super().__init__(parent)
        self._parent = parent
        self._grand_parent = parent._parent  # For a bit of convenience
        self.header = parent.header
        self.database = database
        self.db_map = parent.db_name_to_map[database]
        self._fetched = False
        self._selected_param_def_ids = set()

    def canFetchMore(self, parent=None):
        """Return True if the model hasn't been fetched."""
        return not self._fetched

    def fetchMore(self, parent=None):
        """Get all data from the database and use it to reset the model."""
        source = self.create_source_model()
        self.setSourceModel(source)
        data = self.get_data_from_db()
        source.reset_model(data)
        self._fetched = True

    def create_source_model(self):
        """Returns a model filled with parameter data for the associated entity class."""
        raise NotImplementedError()

    def get_data_from_db(self):
        raise NotImplementedError()

    def batch_set_data(self, indexes, data):
        source_inds = [self.mapToSource(ind) for ind in indexes]
        return self.sourceModel().batch_set_data(source_inds, data)

    def update_filter(self):
        """Updates filter."""
        self.layoutAboutToBeChanged.emit()
        if self.do_update_filter():
            self.invalidateFilter()
        self.layoutChanged.emit()

    def selected_param_def_ids(self):
        raise NotImplementedError()

    def do_update_filter(self):
        """Does update the filter."""
        selected_param_def_ids = self.selected_param_def_ids()
        if selected_param_def_ids != self._selected_param_def_ids:
            self._selected_param_def_ids = selected_param_def_ids
            return True
        return False

    def clear_filter(self):
        """Clears filter."""
        # raise NotImplementedError()

    def filterAcceptsRow(self, source_row, source_parent):
        """Accept or reject row."""
        if not self._main_filter_accepts_row(source_row, source_parent):
            return False
        if not self._auto_filter_accepts_row(source_row, source_parent):
            return False
        return True

    def _main_filter_accepts_row(self, source_row, source_parent):
        if self._selected_param_def_ids:
            parameter_definition_id = self.sourceModel()._main_data[source_row].parameter_definition_id
            return parameter_definition_id in self._selected_param_def_ids
        return True

    def _auto_filter_accepts_row(self, source_row, source_parent):
        return True

    def clear_model(self):
        """Clears model."""
        self.sourceModel().clear_model()
        self._fetched = False


class SingleParameterDefinitionModel(SingleParameterModel):
    """A parameter definition model for a single entity class"""

    def create_source_model(self):
        return FilledParameterDefinitionModel(self._parent)


class SingleObjectParameterDefinitionModel(
    ObjectParameterDecorateMixin, SingleObjectParameterMixin, SingleParameterDefinitionModel
):
    """An object parameter definition model for a single object class."""

    def get_data_from_db(self):
        sq = self.db_map.object_parameter_definition_sq
        return [
            ObjectParameterDefinitionItem(self.header, database=self.database, **param_def._asdict())
            for param_def in self.db_map.query(sq).filter_by(object_class_id=self.object_class_id)
        ]


class SingleRelationshipParameterDefinitionModel(
    RelationshipParameterDecorateMixin, SingleRelationshipParameterMixin, SingleParameterDefinitionModel
):
    """A relationship parameter definition model for a single relationship class."""

    def get_data_from_db(self):
        sq = self.db_map.relationship_parameter_definition_sq
        return [
            RelationshipParameterDefinitionItem(self.header, database=self.database, **param_def._asdict())
            for param_def in self.db_map.query(sq).filter_by(relationship_class_id=self.relationship_class_id)
        ]


class SingleParameterValueModel(SingleParameterModel):
    """A parameter value model for a single entity class"""

    def create_source_model(self):
        return FilledParameterValueModel(self._parent)


class SingleObjectParameterValueModel(
    ObjectParameterDecorateMixin, SingleObjectParameterMixin, SingleParameterValueModel
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

    def do_update_filter(self):
        """Does update the filter."""
        result = super().do_update_filter()
        selected_object_ids = self._grand_parent.selected_object_ids.get((self.db_map, self.object_class_id), {})
        if selected_object_ids != self._selected_object_ids:
            self._selected_object_ids = selected_object_ids
            return True
        return result

    def _main_filter_accepts_row(self, source_row, source_parent):
        """Reimplemented to filter objects."""
        if not super()._main_filter_accepts_row(source_row, source_parent):
            return False
        if self._selected_object_ids:
            object_id = self.sourceModel()._main_data[source_row].object_id
            return object_id in self._selected_object_ids
        return True


class SingleRelationshipParameterValueModel(
    RelationshipParameterDecorateMixin, SingleRelationshipParameterMixin, SingleParameterValueModel
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

    def do_update_filter(self):
        """Does update the filter."""
        cond_a = super().do_update_filter()
        selected_object_id_lists = self._grand_parent.selected_object_id_lists.get(
            (self.db_map, self.relationship_class_id), {}
        )
        selected_object_ids = set(
            obj_id
            for obj_cls_id in self.object_class_id_list
            for obj_id in self._grand_parent.selected_object_ids.get((self.db_map, obj_cls_id), {})
        )
        cond_b = selected_object_id_lists != self._selected_object_id_lists
        cond_c = selected_object_ids != self._selected_object_ids
        if cond_b:
            self._selected_object_id_lists = selected_object_id_lists
        if cond_c:
            self._selected_object_ids = selected_object_ids
        return cond_a or cond_b or cond_c

    def _main_filter_accepts_row(self, source_row, source_parent):
        """Reimplemented to filter relationships and objects."""
        if not super()._main_filter_accepts_row(source_row, source_parent):
            return False
        object_id_list = self.sourceModel()._main_data[source_row].object_id_list
        if self._selected_object_id_lists:
            return object_id_list in self._selected_object_id_lists
        if self._selected_object_ids:
            return bool(self._selected_object_ids.intersection(int(x) for x in object_id_list.split(",")))
        return True
