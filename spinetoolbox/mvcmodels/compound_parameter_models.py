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
Compound models for object parameter definitions and values,
that concatenate several 'single' models and one 'empty' model.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt, Slot, QModelIndex, QSortFilterProxyModel
from PySide2.QtGui import QFont
from helpers import busy_effect, format_string_list
from mvcmodels.minimal_table_model import MinimalTableModel
from mvcmodels.empty_parameter_models import (
    EmptyObjectParameterDefinitionModel,
    EmptyObjectParameterValueModel,
    EmptyRelationshipParameterDefinitionModel,
    EmptyRelationshipParameterValueModel,
)
from mvcmodels.single_parameter_models import (
    SingleObjectParameterDefinitionModel,
    SingleObjectParameterValueModel,
    SingleRelationshipParameterDefinitionModel,
    SingleRelationshipParameterValueModel,
)
from mvcmodels.parameter_item import ObjectParameterValueItem


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
        self.sub_models = []
        self._last_fetched_index = 0  # Index of the last submodel that's already been fetched
        self.filtered_out = dict()
        self.italic_font = QFont()
        self.italic_font.setItalic(True)

    @property
    def single_models(self):
        return self.sub_models[0:-1]

    @property
    def empty_model(self):
        return self.sub_models[-1]

    def canFetchMore(self, parent):
        """Returns True if any of the unfetched single models can fetch more."""
        for model in self.sub_models[self._last_fetched_index :]:
            if model.canFetchMore():
                return True
        return False

    def fetchMore(self, parent):
        """Fetches the next single model and increments the fetched index."""
        self.sub_models[self._last_fetched_index].fetchMore()
        self._last_fetched_index += 1

    def flags(self, index):
        """Translate the index into the corresponding submodel and return its flags."""
        row = index.row()
        column = index.column()
        for model in self.sub_models:
            if row < model.rowCount():
                return model.index(row, column).flags()
            row -= model.rowCount()

    def data(self, index, role=Qt.DisplayRole):
        """Translate the index into the corresponding submodel and return its data."""
        row = index.row()
        column = index.column()
        for model in self.sub_models:
            if row < model.rowCount():
                return model.index(row, column).data(role)
            row -= model.rowCount()

    def rowCount(self, parent=QModelIndex()):
        """Return the sum of rows in all models."""
        return sum(m.rowCount() for m in self.sub_models)

    def insertRows(self, row, count, parent=QModelIndex()):
        """Find the right sub-model (or the empty model) and call insertRows on it."""
        for model in self.sub_models:
            if row < model.rowCount():
                return model.insertRows(row, count)
            row -= model.rowCount()

    def removeRows(self, row, count, parent=QModelIndex()):
        """Distribute the rows among the different submodels
        and call removeRows on each of them.
        """
        if row < 0 or row + count - 1 >= self.rowCount():
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        model_row_set = dict()
        for i in range(row, row + count):
            for model in self.sub_models:
                if i < model.rowCount():
                    model_row_set.setdefault(model, set()).add(i)
                    break
                i -= model.rowCount()
        for model, row_set in model_row_set.items():
            min_row = min(row_set)
            max_row = max(row_set)
            model.removeRows(min_row, max_row - min_row + 1)
        self.endRemoveRows()
        return True

    def item_at_row(self, row):
        """Returns the item at given row."""
        for model in self.sub_models:
            if row < model.rowCount():
                return model.item_at_row(row)
            row -= model.rowCount()

    def batch_set_data(self, indexes, data):
        """Set data for indexes in batch.
        Distribute indexes and values among the different submodels
        and call batch_set_data on each of them."""
        if not indexes or not data:
            return False
        model_index_value = {}  # Maps models to (index, value) tuples
        rows = []
        columns = []
        for index, value in zip(indexes, data):
            if not index.isValid():
                continue
            row = index.row()
            column = index.column()
            rows.append(row)
            columns.append(column)
            for model in self.sub_models:
                if row < model.rowCount():
                    model_index_value.setdefault(model, list()).append((model.index(row, column), value))
                    break
                row -= model.rowCount()
        for model, index_value in model_index_value.items():
            indexes, values = zip(*index_value)
            model.batch_set_data(indexes, values)
        # Find square envelope of indexes to emit dataChanged
        top = min(rows)
        bottom = max(rows)
        left = min(columns)
        right = max(columns)
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right))
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
        Emit rowsInserted as appropriate so we can actually view the new rows.
        """
        offset = self.rowCount() - self.empty_model.rowCount()
        self.rowsInserted.emit(QModelIndex(), offset + first, offset + last)

    def _handle_single_model_reset(self, model):
        """Runs when one of the single models is reset.
        Emit rowsInserted as appropriate so we can actually view the new data.
        """
        first = self.rowCount() + 1
        last = first + model.rowCount() - 1
        self.rowsInserted.emit(QModelIndex(), first, last)

    def invalidate_filter(self):
        """Invalidates filter."""
        self.layoutAboutToBeChanged.emit()
        for model in self.single_models:
            model.invalidateFilter()
        self.layoutChanged.emit()

    @busy_effect
    def auto_filter_values(self, column):
        """Returns values that should be used to populate the auto filter menu
        for the given column.
        Each 'row' in the result has the following three elements:
        1) The 'checked' state, True if the value *hasn't* been filtered out already
        2) The value itself (an object name, a parameter name, a numerical value...)
        3) A set of object class ids where the value is found.
        """
        # TODO

    def set_filtered_out_values(self, column, values):
        """Sets values filtered out by the autofilter."""
        # TODO

    def clear_filter(self):
        """Clears the filter."""
        # TODO

    def rename_object_classes(self, db_map, object_classes):
        """Rename object classes in model."""
        # TODO

    def rename_parameter_tags(self, db_map, parameter_tags):
        """Rename parameter tags in model."""
        # TODO

    def remove_object_classes(self, db_map, object_classes):
        """Remove object classes from model."""
        # TODO

    def remove_parameter_tags(self, db_map, parameter_tag_ids):
        """Remove parameter tags from model."""
        # TODO

    def _emit_data_changed_for_column(self, column):
        """Emits data changed for an entire column.
        Used by `rename_` and some `remove_` methods where it's too difficult to find out the exact
        rows that changed, especially because of filter status.
        """
        # TODO

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
        """Move rows from empty model to a new single model.
        Called when the empty row model succesfully inserts new data in the db.
        """
        self.layoutAboutToBeChanged.emit()
        empty_model = self.sub_models.pop()
        d = {}
        for row in rows:
            item = empty_model.item_at_row(row)
            entity_class = item.entity_class
            database = item.database
            d.setdefault((database, entity_class), list()).append(item)
        single_models = []
        for (database, entity_class), item_list in d.items():
            single_model = self.create_single_model(database, entity_class)
            single_model.reset_model(item_list)
            self._handle_single_model_reset(single_model)
            single_models.append(single_model)
        self.sub_models += single_models
        for row in reversed(rows):
            empty_model.removeRows(row, 1)
        self.sub_models.append(empty_model)
        self.layoutChanged.emit()

    def connect_model_signals(self):
        """Connect model signals."""
        self.empty_model.rowsInserted.connect(self._handle_empty_rows_inserted)
        for model in self.single_models:
            model.modelReset.connect(lambda model=model: self._handle_single_model_reset(model))

    def clear_model(self):
        """Clears model. Runs after rollback or refresh.
        """
        for model in self.sub_models:
            model.clear_model()

    def create_single_model(self, database, db_item):
        """Returns a single model for the given database and item."""
        raise NotImplementedError()

    def create_empty_model(self):
        """Returns an empty model."""
        raise NotImplementedError()

    @staticmethod
    def entity_class_query(db_map):
        """Returns a query of entity classes to populate the model."""
        raise NotImplementedError()

    def update_filter(self):
        """Update filter."""
        self.layoutAboutToBeChanged.emit()
        for model in self.single_models:
            model.clear_filter()  # TODO: rename to `clear_auto_filter`
            model.update_filter()
        self.clear_filter()
        self.layoutChanged.emit()


class CompoundParameterDefinitionModel(CompoundParameterModel):
    """A model that concatenates several single parameter definition models
    and one empty parameter definition model.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.json_fields = ["default_value"]


class CompoundObjectParameterDefinitionModel(CompoundParameterDefinitionModel):
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

    @staticmethod
    def entity_class_query(db_map):
        """Returns a query of object classes to populate the model."""
        return db_map.query(db_map.object_class_sq)


class CompoundRelationshipParameterDefinitionModel(CompoundParameterDefinitionModel):
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

    @staticmethod
    def entity_class_query(db_map):
        """Returns a query of relationship classes to populate the model."""
        return db_map.query(db_map.wide_relationship_class_sq)


class CompoundParameterValueModel(CompoundParameterModel):
    """A model that concatenates several single parameter value models
    and one empty parameter value model.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.json_fields = ["value"]


class CompoundObjectParameterValueModel(CompoundParameterValueModel):
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

    @staticmethod
    def entity_class_query(db_map):
        """Returns a query of object classes to populate the model."""
        return db_map.query(db_map.object_class_sq)


class CompoundRelationshipParameterValueModel(CompoundParameterValueModel):
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

    @staticmethod
    def entity_class_query(db_map):
        """Returns a query of relationship classes to populate the model."""
        return db_map.query(db_map.wide_relationship_class_sq)
