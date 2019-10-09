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
Compound models for object parameter definitions and values.
These models concatenate several 'single' models and one 'empty' model.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt, Slot, QModelIndex
from PySide2.QtGui import QFont
from ..helpers import busy_effect, format_string_list
from ..mvcmodels.compound_table_model import CompoundWithEmptyTableModel
from ..mvcmodels.empty_parameter_models import (
    EmptyObjectParameterDefinitionModel,
    EmptyObjectParameterValueModel,
    EmptyRelationshipParameterDefinitionModel,
    EmptyRelationshipParameterValueModel,
)
from ..mvcmodels.single_parameter_models import (
    SingleObjectParameterDefinitionModel,
    SingleObjectParameterValueModel,
    SingleRelationshipParameterDefinitionModel,
    SingleRelationshipParameterValueModel,
)
from ..mvcmodels.auto_filter_menu_model import AutoFilterMenuItem


class CompoundParameterModel(CompoundWithEmptyTableModel):
    """A model that concatenates several single parameter models
    and one empty parameter model.
    """

    def __init__(self, parent):
        """Init class.

        Args:
            parent (DataStoreForm): an instance of TreeViewForm or GraphViewForm
        """
        super().__init__(parent)
        self._parent = parent
        self.db_name_to_map = parent.db_name_to_map
        self.icon_mngr = parent.icon_mngr
        self._auto_filter = dict()

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Use italic font for columns having an autofilter installed."""
        italic_font = QFont()
        italic_font.setItalic(True)
        if role == Qt.FontRole and orientation == Qt.Horizontal and self._auto_filter.get(section):
            return italic_font
        return super().headerData(section, orientation, role)

    def batch_set_data(self, indexes, data):
        """Set data for indexes in batch.
        Move added rows to single models and emit messages.
        """
        if not super().batch_set_data(indexes, data):
            return False
        added_rows = self.empty_model.added_rows
        updated_count = sum(m.updated_count for m in self.single_models)
        error_log = [entry for m in self.sub_models for entry in m.error_log]
        if added_rows:
            self.move_rows_to_single_models(added_rows)
            self._parent.commit_available.emit(True)
            self._parent.msg.emit(f"Successfully added {len(added_rows)} entries.")
        if updated_count:
            self._parent.commit_available.emit(True)
            self._parent.msg.emit(f"Successfully updated {updated_count} entries.")
        if error_log:
            msg = format_string_list(error_log)
            self._parent.msg_error.emit(msg)
        return True

    @staticmethod
    def entity_class_query(db_map):
        """Returns a query of entity classes to use for creating the different single models."""
        raise NotImplementedError()

    def single_model_keys(self):
        """Generates keys for creating single models when initializing the model."""
        d = dict()
        for database, db_map in self.db_name_to_map.items():
            for entity_class in self.entity_class_query(db_map):
                d.setdefault(entity_class.name, list()).append((database, entity_class))
        for entity_class_list in d.values():
            for database, entity_class in entity_class_list:
                yield (database, entity_class)

    def single_model_key_from_item(self, item):
        """Returns the single model key from the given item.
        Used by move rows to single models.
        """
        return (item.database, item.entity_class)

    def filter_accepts_single_model(self, model):
        """Returns True if the given model should be included in the compound model, otherwise returns False."""
        raise NotImplementedError()

    def accepted_single_models(self):
        """Returns a list of accepted single models, for convenience."""
        return [m for m in self.single_models if self.filter_accepts_single_model(m)]

    @staticmethod
    def _settattr_if_different(obj, attr, val):
        """If the given value is different than the one currently stored
        in the given object, set it and returns True. Otherwise returns False.
        Handy for updating filters.
        """
        curr = getattr(obj, attr)
        if curr != val:
            setattr(obj, attr, val)
            return True
        return False

    def update_filter(self):
        """Update filter."""
        updated = self.update_compound_filter()
        for model in self.single_models:
            updated |= self.update_single_model_filter(model)
        if updated:
            self.refresh()

    def update_compound_filter(self):
        """Update the filter."""
        if not self._auto_filter:
            return False
        self._auto_filter.clear()
        return True

    def update_single_model_filter(self, model):
        """Update the filter for the given model."""
        if not model._auto_filter:
            return False
        model._auto_filter.clear()
        return True

    def _row_map_for_single_model(self, model):
        """Returns row map for given single model.
        Reimplemented to take filter status into account."""
        if not self.filter_accepts_single_model(model):
            return []
        return [(model, i) for i in model.accepted_rows()]

    @busy_effect
    def auto_filter_menu_data(self, column):
        """Returns auto filter menu data for the given column.

        Returns:
            menu_data (list): a list of AutoFilterMenuItem
        """
        auto_filter_vals = dict()
        for model in self.accepted_single_models():
            for row in model.accepted_rows(ignored_columns=[column]):
                value = model._main_data[row][column]
                auto_filter_vals.setdefault(value, set()).add(model.entity_class_id)
        column_auto_filter = self._auto_filter.get(column, {})
        filtered = [val for values in column_auto_filter.values() for val in values]
        return [
            AutoFilterMenuItem(Qt.Checked if value not in filtered else Qt.Unchecked, value, in_classes)
            for value, in_classes in auto_filter_vals.items()
        ]

    def update_auto_filter(self, column, auto_filter):
        """Updates auto filter for given column.

        Args:
            column (int): the column number
            auto_filter (dict): maps entity ids to a collection of values to be filtered for the column
        """
        self._auto_filter[column] = auto_filter
        updated = False
        for model in self.accepted_single_models():
            updated |= self.update_single_model_auto_filter(model, column)
        if updated:
            self.refresh()

    def update_single_model_auto_filter(self, model, column):
        """Set auto filter values for given column.

        Args:
            model (SingleParameterModel): the model
            column (int): the column number
        """
        values = self._auto_filter[column].get(model.entity_class_id, {})
        if values == model._auto_filter.get(column, {}):
            return False
        model._auto_filter[column] = values
        return True

    def _emit_data_changed_for_column(self, field):
        """Emits data changed for an entire column.
        Used by `rename_` and some `remove_` methods because we're too lazy
        to find out the exact rows that changed.

        Args:
            field (str): the column header
        """
        try:
            column = self.header.index(field)
        except ValueError:
            pass
        else:
            self.dataChanged.emit(self.index(0, column), self.index(self.rowCount() - 1, column), [Qt.DisplayRole])

    def _models_with_db_map(self, db_map):
        """Returns a collection of models having the given db_map."""
        return (m for m in self.single_models if m.db_map == db_map)


class CompoundObjectParameterMixin:
    """Implements the interface for populating and filtering a compound object parameter model."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_object_class_ids = None

    def update_compound_filter(self):
        """Update the filter."""
        a = super().update_compound_filter()
        b = self._settattr_if_different(self, "_selected_object_class_ids", self._parent.all_selected_object_class_ids)
        return a or b

    def filter_accepts_single_model(self, model):
        """Returns True if the given model should be included in the compound model, otherwise returns False.
        """
        if not self._selected_object_class_ids:
            return True
        return model.object_class_id in self._selected_object_class_ids.get(model.db_map, set())

    def update_single_model_filter(self, model):
        """Update the filter for a single model."""
        a = super().update_single_model_filter(model)
        b = self._settattr_if_different(
            model,
            "_selected_param_def_ids",
            self._parent.selected_obj_parameter_definition_ids.get((model.db_map, model.object_class_id), set()),
        )
        return a or b

    @staticmethod
    def entity_class_query(db_map):
        """Returns a query of object classes to populate the model."""
        return db_map.query(db_map.object_class_sq)


class CompoundRelationshipParameterMixin:
    """Implements the interface for populating and filtering a compound relationship parameter model."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_object_class_ids = None
        self._selected_relationship_class_ids = None

    def update_compound_filter(self):
        """Update the filter."""
        a = super().update_compound_filter()
        b = self._settattr_if_different(self, "_selected_object_class_ids", self._parent.selected_object_class_ids)
        c = self._settattr_if_different(
            self, "_selected_relationship_class_ids", self._parent.all_selected_relationship_class_ids
        )
        return a or b or c

    def filter_accepts_single_model(self, model):
        """Returns True if the given single model should be included in the compound model, otherwise returns False.
        """
        return (
            not self._selected_object_class_ids
            or self._selected_object_class_ids.get(model.db_map, set()).intersection(model.object_class_id_list)
        ) and (
            not self._selected_relationship_class_ids
            or model.relationship_class_id in self._selected_relationship_class_ids.get(model.db_map, set())
        )

    def update_single_model_filter(self, model):
        """Update the filter for a single model."""
        a = super().update_single_model_filter(model)
        b = self._settattr_if_different(
            model,
            "_selected_param_def_ids",
            self._parent.selected_rel_parameter_definition_ids.get((model.db_map, model.relationship_class_id), set()),
        )
        return a or b

    @staticmethod
    def entity_class_query(db_map):
        """Returns a query of relationship classes to populate the model."""
        return db_map.query(db_map.wide_relationship_class_sq)


class CompoundObjectParameterRenameRemoveMixin:
    """Implements an interface to rename and remove items in a compound object parameter model."""

    def rename_object_classes(self, db_map, object_classes):
        """Rename object classes in model."""
        object_classes = {x.id: x.name for x in object_classes}
        for model in self._models_with_db_map(db_map):
            model.rename_object_classes(object_classes)
        self._emit_data_changed_for_column("object_class_name")

    def remove_object_classes(self, db_map, object_classes):
        """Remove object classes from model."""
        object_class_ids = [x['id'] for x in object_classes]
        for model in self._models_with_db_map(db_map):
            if model.object_class_id in object_class_ids:
                self.sub_models.remove(model)
        self.refresh()


class CompoundRelationshipParameterRenameRemoveMixin:
    """Implements an interface to rename and remove items in a compound relationship parameter model."""

    def rename_relationship_classes(self, db_map, relationship_classes):
        """Rename relationship classes in model."""
        relationship_classes = {x.id: x.name for x in relationship_classes}
        for model in self._models_with_db_map(db_map):
            model.rename_relationship_classes(relationship_classes)
        self._emit_data_changed_for_column("relationship_class_name")

    def remove_relationship_classes(self, db_map, relationship_classes):
        """Remove relationship classes from model."""
        relationship_class_ids = {x['id'] for x in relationship_classes}
        for model in self._models_with_db_map(db_map):
            if model.relationship_class_id in relationship_class_ids:
                self.sub_models.remove(model)
        self.refresh()

    def rename_object_classes(self, db_map, object_classes):
        """Rename object classes in model."""
        object_classes = {x.id: x.name for x in object_classes}
        for model in self._models_with_db_map(db_map):
            model.rename_object_classes(object_classes)
        self._emit_data_changed_for_column("object_class_name_list")

    def remove_object_classes(self, db_map, object_classes):
        """Remove object classes from model."""
        object_class_ids = {x['id'] for x in object_classes}
        for model in self._models_with_db_map(db_map):
            if object_class_ids.intersection(model.object_class_id_list):
                self.sub_models.remove(model)
        self.refresh()


class CompoundParameterDefinitionRenameRemoveMixin:
    """Implements an interface to rename and remove items in a compound parameter definition model."""

    def rename_parameter_tags(self, db_map, parameter_tags):
        """Rename parameter tags in model."""
        parameter_tags = {x.id: x.tag for x in parameter_tags}
        for model in self._models_with_db_map(db_map):
            model.rename_parameter_tags(parameter_tags)
        self._emit_data_changed_for_column("parameter_tag_list")

    def remove_parameter_tags(self, db_map, parameter_tag_ids):
        """Remove parameter tags from model."""
        for model in self._models_with_db_map(db_map):
            model.remove_parameter_tags(parameter_tag_ids)
        self._emit_data_changed_for_column("parameter_tag_list")

    def rename_parameter_value_lists(self, db_map, value_lists):
        """Rename parameter value_lists in model."""
        value_lists = {x.id: x.name for x in value_lists}
        for model in self._models_with_db_map(db_map):
            model.rename_parameter_value_lists(parameter_tags)
        self._emit_data_changed_for_column("value_list_name")

    def clear_parameter_value_lists(self, db_map, value_list_ids):
        """Clear parameter value_lists from model."""
        for model in self._models_with_db_map(db_map):
            model.clear_parameter_value_lists(value_list_ids)
        self._emit_data_changed_for_column("value_list_name")


class CompoundParameterValueRenameRemoveMixin:
    """Implements an interface to rename and remove items in a compound parameter value model."""

    def rename_parameters(self, db_map, parameters):
        """Rename parameters in model."""
        parameters = {x['id']: x['name'] for x in parameters}
        for model in self._models_with_db_map(db_map):
            model.rename_parameters(parameters)
        self._emit_data_changed_for_column("parameter_name")

    def remove_parameters(self, db_map, parameters):
        """Remove parameters from model."""
        parameter_ids = {}
        for parameter in parameters:
            parameter_ids.setdefault(parameter["entity_class_id"], set()).add(parameter['id'])
        for model in self._models_with_db_map(db_map):
            class_parameter_ids = parameter_ids.get(model.entity_class_id)
            if not class_parameter_ids:
                continue
            for row in reversed(range(model.rowCount())):
                parameter_id = model._main_data[row].parameter_id
                if parameter_id in class_parameter_ids:
                    model.removeRows(row, 1)
        self.refresh()


class CompoundObjectParameterValueRenameRemoveMixin:
    """Implements an interface to rename and remove items in a compound object parameter value model."""

    def rename_objects(self, db_map, objects):
        """Rename objects in model."""
        objects = {x.id: x.name for x in objects}
        for model in self._models_with_db_map(db_map):
            model.rename_objects(objects)
        self._emit_data_changed_for_column("object_name")

    def remove_objects(self, db_map, objects):
        """Remove objects from model."""
        object_ids = {}
        for object_ in objects:
            object_ids.setdefault(object_["class_id"], set()).add(object_['id'])
        for model in self._models_with_db_map(db_map):
            class_object_ids = object_ids.get(model.entity_class_id)
            if not class_object_ids:
                continue
            for row in reversed(range(model.rowCount())):
                object_id = model._main_data[row].object_id
                if object_id in class_object_ids:
                    model.removeRows(row, 1)
        self.refresh()


class CompoundRelationshipParameterValueRenameRemoveMixin:
    """Implements an interface to rename and remove items in a compound relationship parameter value model."""

    def rename_objects(self, db_map, objects):
        """Rename objects in model."""
        objects = {x.id: x.name for x in objects}
        for model in self._models_with_db_map(db_map):
            model.rename_objects(objects)
        self._emit_data_changed_for_column("object_name_list")

    def remove_objects(self, db_map, objects):
        """Remove objects from model."""
        object_ids = {}
        for object_ in objects:
            object_ids.setdefault(object_['class_id'], set()).add(object_['id'])
        for model in self._models_with_db_map(db_map):
            class_object_ids = {id_ for class_id in model.object_class_id_list for id_ in object_ids.get(class_id, [])}
            if not class_object_ids:
                continue
            for row in reversed(range(model.rowCount())):
                object_id_list = model._main_data[row].object_id_list
                object_id_list = [int(id_) for id_ in object_id_list.split(",")]
                if class_object_ids.intersection(object_id_list):
                    model.removeRows(row, 1)
        self.refresh()

    def remove_relationships(self, db_map, relationships):
        """Remove relationships from model."""
        relationship_ids = {}
        for relationship in relationships:
            relationship_ids.setdefault(relationship["class_id"], set()).add(relationship['id'])
        for model in self._models_with_db_map(db_map):
            class_relationship_ids = relationship_ids.get(model.entity_class_id)
            if not class_relationship_ids:
                continue
            for row in reversed(range(model.rowCount())):
                relationship_id = model._main_data[row].relationship_id
                if relationship_id in class_relationship_ids:
                    model.removeRows(row, 1)
        self.refresh()


class CompoundObjectParameterDefinitionModel(
    CompoundObjectParameterMixin,
    CompoundObjectParameterRenameRemoveMixin,
    CompoundParameterDefinitionRenameRemoveMixin,
    CompoundParameterModel,
):
    """A model that concatenates several single object parameter definition models
    and one empty object parameter definition model.
    """

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self.header = [
            "object_class_name",
            "parameter_name",
            "value_list_name",
            "parameter_tag_list",
            "default_value",
            "database",
        ]
        self.fixed_fields = ["object_class_name", "database"]
        self.json_fields = ["default_value"]

    def create_single_model(self, database, db_item):
        return SingleObjectParameterDefinitionModel(
            self,
            database,
            db_item.id,
            header=self.header,
            fixed_fields=self.fixed_fields,
            json_fields=self.json_fields,
            icon_mngr=self.icon_mngr,
        )

    def create_empty_model(self):
        return EmptyObjectParameterDefinitionModel(self, header=self.header, icon_mngr=self.icon_mngr)


class CompoundRelationshipParameterDefinitionModel(
    CompoundRelationshipParameterMixin,
    CompoundRelationshipParameterRenameRemoveMixin,
    CompoundParameterDefinitionRenameRemoveMixin,
    CompoundParameterModel,
):
    """A model that concatenates several single relationship parameter definition models
    and one empty relationship parameter definition model.
    """

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self.header = [
            "relationship_class_name",
            "object_class_name_list",
            "parameter_name",
            "value_list_name",
            "parameter_tag_list",
            "default_value",
            "database",
        ]
        self.fixed_fields = ["relationship_class_name", "object_class_name_list", "database"]
        self.json_fields = ["default_value"]

    def create_single_model(self, database, db_item):
        return SingleRelationshipParameterDefinitionModel(
            self,
            database,
            db_item.id,
            db_item.object_class_id_list,
            header=self.header,
            fixed_fields=self.fixed_fields,
            json_fields=self.json_fields,
            icon_mngr=self.icon_mngr,
        )

    def create_empty_model(self):
        return EmptyRelationshipParameterDefinitionModel(self, header=self.header, icon_mngr=self.icon_mngr)


class CompoundObjectParameterValueModel(
    CompoundObjectParameterMixin,
    CompoundObjectParameterRenameRemoveMixin,
    CompoundParameterValueRenameRemoveMixin,
    CompoundObjectParameterValueRenameRemoveMixin,
    CompoundParameterModel,
):
    """A model that concatenates several single object parameter value models
    and one empty object parameter value model.
    """

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self.header = ["object_class_name", "object_name", "parameter_name", "value", "database"]
        self.fixed_fields = ["object_class_name", "object_name", "parameter_name", "database"]
        self.json_fields = ["value"]

    def create_single_model(self, database, db_item):
        return SingleObjectParameterValueModel(
            self,
            database,
            db_item.id,
            header=self.header,
            fixed_fields=self.fixed_fields,
            json_fields=self.json_fields,
            icon_mngr=self.icon_mngr,
        )

    def create_empty_model(self):
        return EmptyObjectParameterValueModel(self, header=self.header, icon_mngr=self.icon_mngr)

    def update_single_model_filter(self, model):
        """Update the filter for the given model."""
        a = super().update_single_model_filter(model)
        b = self._settattr_if_different(
            model,
            "_selected_object_ids",
            self._parent.selected_object_ids.get((model.db_map, model.object_class_id), set()),
        )
        return a or b


class CompoundRelationshipParameterValueModel(
    CompoundRelationshipParameterMixin,
    CompoundRelationshipParameterRenameRemoveMixin,
    CompoundParameterValueRenameRemoveMixin,
    CompoundRelationshipParameterValueRenameRemoveMixin,
    CompoundParameterModel,
):
    """A model that concatenates several single relationship parameter value models
    and one empty relationship parameter value model.
    """

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self.header = ["relationship_class_name", "object_name_list", "parameter_name", "value", "database"]
        self.fixed_fields = ["relationship_class_name", "object_name_list", "parameter_name", "database"]
        self.json_fields = ["value"]

    def create_single_model(self, database, db_item):
        return SingleRelationshipParameterValueModel(
            self,
            database,
            db_item.id,
            db_item.object_class_id_list,
            header=self.header,
            fixed_fields=self.fixed_fields,
            json_fields=self.json_fields,
            icon_mngr=self.icon_mngr,
        )

    def create_empty_model(self):
        return EmptyRelationshipParameterValueModel(self, header=self.header, icon_mngr=self.icon_mngr)

    def update_single_model_filter(self, model):
        """Update the filter for the given model."""
        a = super().update_single_model_filter(model)
        b = self._settattr_if_different(
            model,
            "_selected_object_id_lists",
            self._parent.selected_object_id_lists.get((model.db_map, model.relationship_class_id), set()),
        )
        c = self._settattr_if_different(
            model,
            "_selected_object_ids",
            set(
                obj_id
                for obj_cls_id in model.object_class_id_list
                for obj_id in self._parent.selected_object_ids.get((model.db_map, obj_cls_id), set())
            ),
        )
        return a or b or c
