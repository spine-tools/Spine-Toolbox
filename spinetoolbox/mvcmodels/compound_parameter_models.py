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

from PySide2.QtCore import Qt, Slot, QModelIndex, QSortFilterProxyModel
from PySide2.QtGui import QFont
from ..helpers import busy_effect, format_string_list, rows_to_row_count_tuples
from ..mvcmodels.minimal_table_model import MinimalTableModel
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
from ..mvcmodels.parameter_mixins import CompoundObjectParameterMixin, CompoundRelationshipParameterMixin
from ..mvcmodels.auto_filter_menu_model import AutoFilterMenuItem


class CompoundParameterModel(MinimalTableModel):
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
        self.db_maps = parent.db_maps
        self.db_name_to_map = parent.db_name_to_map
        self.icon_mngr = parent.icon_mngr
        self.sub_models = []
        self._row_map = []
        self._fetched_count = 0  # Index of the last submodel that's already been fetched
        self._auto_filter = dict()

    @property
    def single_models(self):
        return self.sub_models[0:-1]

    @property
    def empty_model(self):
        return self.sub_models[-1]

    def canFetchMore(self, parent):
        """Returns True if any of the unfetched single models can fetch more."""
        for model in self.sub_models[self._fetched_count :]:
            if model.canFetchMore():
                return True
        return False

    def fetchMore(self, parent):
        """Fetches the next single model and increments the fetched index."""
        self.sub_models[self._fetched_count].fetchMore()
        self._fetched_count += 1

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Use italic font for columns having an autofilter installed."""
        italic_font = QFont()
        italic_font.setItalic(True)
        if role == Qt.FontRole and orientation == Qt.Horizontal and self._auto_filter.get(section):
            return italic_font
        return super().headerData(section, orientation, role)

    def map_to_sub(self, index):
        """Returns a submodel index corresponding to given one."""
        row = index.row()
        column = index.column()
        sub_model, sub_row = self._row_map[row]
        return sub_model.index(sub_row, column)

    def flags(self, index):
        """Translate the index into the corresponding submodel and return its flags."""
        return self.map_to_sub(index).flags()

    def data(self, index, role=Qt.DisplayRole):
        """Maps the index into a submodel and return its data."""
        return self.map_to_sub(index).data(role)

    def rowCount(self, parent=QModelIndex()):
        """Return the sum of rows in all models."""
        return len(self._row_map)

    def removeRows(self, row, count, parent=QModelIndex()):
        """Distribute the rows among the different submodels
        and call removeRows on each of them.
        """
        if row < 0 or row + count - 1 >= self.rowCount():
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        d = dict()
        for sub_model, sub_row in self._row_map[row, row + count]:
            d.setdefault(sub_model, list()).append(sub_row)
        for sub_model, sub_rows in d.items():
            for sub_row, sub_count in rows_to_row_count_tuples(sub_rows):
                sub_model.removeRows(sub_row, sub_count)
        self.endRemoveRows()
        return True

    def item_at_row(self, row):
        """Returns the item at given row."""
        sub_model, sub_row = self._row_map[row]
        return sub_model.item_at_row(sub_row)

    def batch_set_data(self, indexes, data):
        """Set data for indexes in batch.
        Distribute indexes and values among the different submodels
        and call batch_set_data on each of them."""
        if not indexes or not data:
            return False
        d = {}  # Maps models to (index, value) tuples
        rows = []
        columns = []
        for index, value in zip(indexes, data):
            if not index.isValid():
                continue
            rows.append(index.row())
            columns.append(index.column())
            sub_model, _ = self._row_map[index.row()]
            sub_index = self.map_to_sub(index)
            d.setdefault(sub_model, list()).append((sub_index, value))
        for model, index_value_tuples in d.items():
            indexes, values = zip(*index_value_tuples)
            model.batch_set_data(indexes, values)
        # Find square envelope of indexes to emit dataChanged
        top = min(rows)
        bottom = max(rows)
        left = min(columns)
        right = max(columns)
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right))
        # React to what's just happened
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

    @Slot("QModelIndex", "int", "int", name="_handle_empty_rows_inserted")
    def _handle_empty_rows_inserted(self, parent, first, last):
        """Runs when rows are inserted to the empty model.
        Update row_map, then emit rowsInserted so the new rows become visible.
        """
        self._row_map += [(self.empty_model, i) for i in range(first, last + 1)]
        tip = self.rowCount() - self.empty_model.rowCount()
        self.rowsInserted.emit(QModelIndex(), tip + first, tip + last)

    @Slot("QModelIndex", "int", "int", name="_handle_empty_rows_removed")
    def _handle_empty_rows_removed(self, parent, first, last):
        """Runs when rows are inserted to the empty model.
        Update row_map, then emit rowsRemoved so the removed rows are no longer visible.
        """
        removed_count = last - first + 1
        tip = self.rowCount() - (self.empty_model.rowCount() + removed_count)
        self._row_map = self._row_map[:tip] + [(self.empty_model, i) for i in range(self.empty_model.rowCount())]
        self.rowsRemoved.emit(QModelIndex(), tip + first, tip + last)

    def _handle_single_model_reset(self, model):
        """Runs when one of the single models is reset.
        Update row_map, then emit rowsInserted so the new rows become visible.
        """
        tip = self.rowCount() - self.empty_model.rowCount()
        self._row_map, empty_row_map = self._row_map[:tip], self._row_map[tip:]
        self._row_map += [(model, i) for i in range(model.rowCount())] + empty_row_map
        first = self.rowCount() + 1
        last = first + model.rowCount() - 1
        self.rowsInserted.emit(QModelIndex(), first, last)

    def create_single_model(self, database, db_item):
        """Returns a single model for the given database and item."""
        raise NotImplementedError()

    def create_empty_model(self):
        """Returns an empty model."""
        raise NotImplementedError()

    @staticmethod
    def entity_class_query(db_map):
        """Returns a query of entity classes to use for creating the different single models."""
        raise NotImplementedError()

    def init_model(self):
        """Initialize model."""
        d = dict()
        for database, db_map in self.db_name_to_map.items():
            for entity_class in self.entity_class_query(db_map):
                d.setdefault(entity_class.name, list()).append((database, entity_class))
        self.sub_models = [
            self.create_single_model(database, entity_class)
            for entity_class_list in d.values()
            for database, entity_class in entity_class_list
        ]
        self.sub_models.append(self.create_empty_model())
        self.connect_model_signals()

    def move_rows_to_single_models(self, rows):
        """Move rows with newly added items from the empty model to a new single model.
        Runs when the empty row model succesfully inserts new data into the db.
        """
        d = {}
        for row in rows:
            item = self.empty_model.item_at_row(row)
            d.setdefault((item.database, item.entity_class), list()).append(item)
        single_models = []
        for (database, entity_class), item_list in d.items():
            single_model = self.create_single_model(database, entity_class)
            single_model.reset_model(item_list)
            self._handle_single_model_reset(single_model)
            single_models.append(single_model)
        pos = len(self.single_models)
        self.sub_models[pos:pos] = single_models
        for row in reversed(rows):
            self.empty_model.removeRows(row, 1)

    def connect_model_signals(self):
        """Connect model signals."""
        self.empty_model.rowsInserted.connect(self._handle_empty_rows_inserted)
        self.empty_model.rowsRemoved.connect(self._handle_empty_rows_removed)
        for model in self.single_models:
            model.modelReset.connect(lambda model=model: self._handle_single_model_reset(model))

    def clear_model(self):
        """Clears model. Runs after rollback or refresh."""
        # TODO: Use this
        for model in self.sub_models:
            model.clear_model()

    def filter_accepts_single_model(self, model):
        """Returns True if the given model should be included in the compound model, otherwise returns False."""
        raise NotImplementedError()

    def accepted_single_models(self):
        """Returns a list of accepted single models, for convenience."""
        return [m for m in self.single_models if self.filter_accepts_single_model(m)]

    @staticmethod
    def _settattr_if_different(obj, attr, val):
        """If the given value is different than the one currently stored
        in the given object, set it and returns True.
        Otherwise returns False.
        """
        curr = getattr(obj, attr)
        if curr != val:
            setattr(obj, attr, val)
            return True
        return False

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

    def update_filter(self):
        """Update filter."""
        updated = self.update_compound_filter()
        for model in self.single_models:
            updated |= self.update_single_model_filter(model)
        if updated:
            self.apply_filter()

    def apply_filter(self):
        """Applies the current filter.
        Recompute the row map taking into account filter results.
        """
        self.layoutAboutToBeChanged.emit()
        self._row_map.clear()
        for model in self.accepted_single_models():
            self._row_map += [(model, i) for i in model.accepted_rows()]
        self._row_map += [(self.empty_model, i) for i in range(self.empty_model.rowCount())]
        self.layoutChanged.emit()

    @busy_effect
    def auto_filter_menu_data(self, column):
        """Returns auto filter menu data for the given column.

        Returns:
            menu_data (list): a list of AutoFilterMenuItem
        """
        auto_filter_vals = dict()
        for model in self.accepted_single_models():
            row_count = model.rowCount()
            for i in range(model.rowCount()):
                if not model._main_filter_accepts_row(i):
                    continue
                if not model._auto_filter_accepts_row(i, ignored_columns=[column]):
                    continue
                value = model._main_data[i][column]
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
        self.apply_filter()

    def update_single_model_auto_filter(self, model, column):
        """Set auto filter values for given column.

        Args:
            model (SingleParameterModel): the model
            column (int): the column number
            values (set): the set of values to be filtered
        """
        values = self._auto_filter[column].get(model.entity_class_id, {})
        if values == model._auto_filter.get(column, {}):
            return False
        model._auto_filter[column] = values
        return True

    def _emit_data_changed_for_column(self, field):
        """Emits data changed for an entire column.
        Used by `rename_` and some `remove_` methods whenever it's too difficult to find out the exact
        rows that changed, especially because of filter status.

        Args:
            field (str): the column header
        """
        column = self.header.index(field)
        self.dataChanged.emit(self.index(0, column), self.index(self.rowCount() - 1, column), [Qt.DisplayRole])

    def _models_with_db_map(self, db_map):
        """Returns a collection of models having the given db_map."""
        return (m for m in self.single_models if m.db_map == db_map)


class CompoundParameterDefinitionModel(CompoundParameterModel):
    """A model that concatenates several single parameter definition models
    and one empty parameter definition model.
    """

    def __init__(self, parent):
        """Init class."""
        super().__init__(parent)
        self.json_fields = ["default_value"]

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


class CompoundObjectParameterDefinitionModel(CompoundObjectParameterMixin, CompoundParameterDefinitionModel):
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

    def create_single_model(self, database, db_item):
        return SingleObjectParameterDefinitionModel(self, database, db_item.id)

    def create_empty_model(self):
        return EmptyObjectParameterDefinitionModel(self)


class CompoundRelationshipParameterDefinitionModel(
    CompoundRelationshipParameterMixin, CompoundParameterDefinitionModel
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

    def create_single_model(self, database, db_item):
        return SingleRelationshipParameterDefinitionModel(self, database, db_item.id, db_item.object_class_id_list)

    def create_empty_model(self):
        return EmptyRelationshipParameterDefinitionModel(self)


class CompoundParameterValueModel(CompoundParameterModel):
    """A model that concatenates several single parameter value models
    and one empty parameter value model.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.json_fields = ["value"]


class CompoundObjectParameterValueModel(CompoundObjectParameterMixin, CompoundParameterValueModel):
    """A model that concatenates several single object parameter value models
    and one empty object parameter value model.
    """

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self.header = ["object_class_name", "object_name", "parameter_name", "value", "database"]
        self.fixed_fields = ["object_class_name", "object_name", "parameter_name", "database"]

    def create_single_model(self, database, db_item):
        return SingleObjectParameterValueModel(self, database, db_item.id)

    def create_empty_model(self):
        return EmptyObjectParameterValueModel(self)

    def update_single_model_filter(self, model):
        """Update the filter for the given model."""
        a = super().update_single_model_filter(model)
        b = self._settattr_if_different(
            model,
            "_selected_object_ids",
            self._parent.selected_object_ids.get((model.db_map, model.object_class_id), set()),
        )
        return a or b


class CompoundRelationshipParameterValueModel(CompoundRelationshipParameterMixin, CompoundParameterValueModel):
    """A model that concatenates several single relationship parameter value models
    and one empty relationship parameter value model.
    """

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self.header = ["relationship_class_name", "object_name_list", "parameter_name", "value", "database"]
        self.fixed_fields = ["relationship_class_name", "object_name_list", "parameter_name", "database"]

    def create_single_model(self, database, db_item):
        return SingleRelationshipParameterValueModel(self, database, db_item.id, db_item.object_class_id_list)

    def create_empty_model(self):
        return EmptyRelationshipParameterValueModel(self)

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
