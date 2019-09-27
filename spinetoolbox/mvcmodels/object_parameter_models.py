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
Models for object parameter definitions and values.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt, Slot, QModelIndex, QSortFilterProxyModel
from PySide2.QtGui import QFont
from ..helpers import busy_effect, format_string_list
from .minimal_table_model import MinimalTableModel
from .empty_parameter_models import EmptyObjectParameterValueModel, EmptyObjectParameterDefinitionModel
from .sub_parameter_models import SubParameterValueModel, SubParameterDefinitionModel


class ObjectParameterModel(MinimalTableModel):
    """A model that concatenates several 'sub' object parameter models,
    one per object class.
    """

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self._parent = parent
        self.db_maps = parent.db_maps
        self.db_name_to_map = parent.db_name_to_map
        self.sub_models = []
        self.empty_row_model = None
        self.fixed_columns = list()
        self.filtered_out = dict()
        self.italic_font = QFont()
        self.italic_font.setItalic(True)

    def flags(self, index):
        """Return flags for given index.
        Depending on the index's row we will land on a specific model.
        Models whose object class id is not selected are skipped.
        """
        row = index.row()
        column = index.column()
        selected_object_class_ids = self._parent.all_selected_object_class_ids()
        for object_class_id, model in self.sub_models:
            if selected_object_class_ids and object_class_id not in selected_object_class_ids:
                continue
            if row < model.rowCount():
                return model.index(row, column).flags()
            row -= model.rowCount()
        return self.empty_row_model.index(row, column).flags()

    def data(self, index, role=Qt.DisplayRole):
        """Return data for given index and role.
        Depending on the index's row we will land on a specific model.
        Models whose object class id is not selected are skipped.
        """
        row = index.row()
        column = index.column()
        selected_object_class_ids = self._parent.all_selected_object_class_ids()
        for object_class_id, model in self.sub_models:
            if selected_object_class_ids and object_class_id not in selected_object_class_ids:
                continue
            if row < model.rowCount():
                if role == Qt.DecorationRole and column == self.object_class_name_column:
                    object_class_name = model.index(row, column).data(Qt.DisplayRole)
                    return self._parent.icon_mngr.object_icon(object_class_name)
                return model.index(row, column).data(role)
            row -= model.rowCount()
        if role == Qt.DecorationRole and column == self.object_class_name_column:
            object_class_name = self.empty_row_model.index(row, column).data(Qt.DisplayRole)
            return self._parent.icon_mngr.object_icon(object_class_name)
        return self.empty_row_model.index(row, column).data(role)

    def rowCount(self, parent=QModelIndex()):
        """Return the sum of rows in all models.
        Skip models whose object class id is not selected.
        """
        count = 0
        selected_object_class_ids = self._parent.all_selected_object_class_ids()
        for object_class_id, model in self.sub_models:
            if selected_object_class_ids and object_class_id not in selected_object_class_ids:
                continue
            count += model.rowCount()
        count += self.empty_row_model.rowCount()
        return count

    def batch_set_data(self, indexes, data):
        """Batch set data for indexes.
        Distribute indexes and data among the different submodels
        and call batch_set_data on each of them."""
        if not indexes:
            return False
        if len(indexes) != len(data):
            return False
        model_indexes = {}
        model_data = {}
        selected_object_class_ids = self._parent.all_selected_object_class_ids()
        for k, index in enumerate(indexes):
            if not index.isValid():
                continue
            row = index.row()
            column = index.column()
            for object_class_id, model in self.sub_models:
                if selected_object_class_ids and object_class_id not in selected_object_class_ids:
                    continue
                if row < model.rowCount():
                    model_indexes.setdefault(model, list()).append(model.index(row, column))
                    model_data.setdefault(model, list()).append(data[k])
                    break
                row -= model.rowCount()
            else:
                model = self.empty_row_model
                model_indexes.setdefault(model, list()).append(model.index(row, column))
                model_data.setdefault(model, list()).append(data[k])
        updated_count = 0
        update_error_log = []
        for _, model in self.sub_models:
            model.batch_set_data(model_indexes.get(model, list()), model_data.get(model, list()))
            updated_count += model.sourceModel().updated_count
            update_error_log += model.sourceModel().error_log
        model = self.empty_row_model
        model.batch_set_data(model_indexes.get(model, list()), model_data.get(model, list()))
        add_error_log = model.error_log
        added_rows = model.added_rows
        # Find square envelope of indexes to emit dataChanged
        top = min(ind.row() for ind in indexes)
        bottom = max(ind.row() for ind in indexes)
        left = min(ind.column() for ind in indexes)
        right = max(ind.column() for ind in indexes)
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right))
        if added_rows:
            self.move_rows_to_sub_models(added_rows)
            self._parent.commit_available.emit(True)
            self._parent.msg.emit("Successfully added entries.")
        if updated_count:
            self._parent.commit_available.emit(True)
            self._parent.msg.emit("Successfully updated entries.")
        error_log = add_error_log + update_error_log
        if error_log:
            msg = format_string_list(error_log)
            self._parent.msg_error.emit(msg)
        return True

    def insertRows(self, row, count, parent=QModelIndex()):
        """Find the right sub-model (or the empty model) and call insertRows on it."""
        selected_object_class_ids = self._parent.all_selected_object_class_ids()
        for object_class_id, model in self.sub_models:
            if selected_object_class_ids and object_class_id not in selected_object_class_ids:
                continue
            if row < model.rowCount():
                return model.insertRows(row, count)
            row -= model.rowCount()
        return self.empty_row_model.insertRows(row, count)

    def removeRows(self, row, count, parent=QModelIndex()):
        """Find the right sub-models (or empty model) and call removeRows on them."""
        if row < 0 or row + count - 1 >= self.rowCount():
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        selected_object_class_ids = self._parent.all_selected_object_class_ids()
        model_row_sets = dict()
        for i in range(row, row + count):
            for object_class_id, model in self.sub_models:
                if selected_object_class_ids and object_class_id not in selected_object_class_ids:
                    continue
                if i < model.rowCount():
                    model_row_sets.setdefault(model, set()).add(i)
                    break
                i -= model.rowCount()
            else:
                model_row_sets.setdefault(self.empty_row_model, set()).add(i)
        for _, model in self.sub_models:
            try:
                row_set = model_row_sets[model]
                min_row = min(row_set)
                max_row = max(row_set)
                model.removeRows(min_row, max_row - min_row + 1)
            except KeyError:
                pass
        try:
            row_set = model_row_sets[self.empty_row_model]
            min_row = min(row_set)
            max_row = max(row_set)
            self.empty_row_model.removeRows(min_row, max_row - min_row + 1)
        except KeyError:
            pass
        self.endRemoveRows()
        return True

    @Slot("QModelIndex", "int", "int", name="_handle_empty_rows_inserted")
    def _handle_empty_rows_inserted(self, parent, first, last):
        offset = self.rowCount() - self.empty_row_model.rowCount()
        self.rowsInserted.emit(QModelIndex(), offset + first, offset + last)

    def invalidate_filter(self):
        """Invalidate filter."""
        self.layoutAboutToBeChanged.emit()
        for _, model in self.sub_models:
            model.invalidateFilter()
        self.layoutChanged.emit()

    @busy_effect
    def auto_filter_values(self, column):
        """Return values to populate the auto filter of given column.
        Each 'row' in the returned value consists of:
        1) The 'checked' state, True if the value *hasn't* been filtered out
        2) The value itself (an object name, a parameter name, a numerical value...)
        3) A set of object class ids where the value is found.
        """
        values = dict()
        selected_object_class_ids = self._parent.all_selected_object_class_ids()
        for object_class_id, model in self.sub_models:
            if selected_object_class_ids and object_class_id not in selected_object_class_ids:
                continue
            data = model.sourceModel()._main_data
            row_count = model.sourceModel().rowCount()
            for i in range(row_count):
                if not model.main_filter_accepts_row(i, None):
                    continue
                if not model.auto_filter_accepts_row(i, None, ignored_columns=[column]):
                    continue
                values.setdefault(data[i][column], set()).add(object_class_id)
        filtered_out = self.filtered_out.get(column, [])
        return [[val not in filtered_out, val, obj_cls_id_set] for val, obj_cls_id_set in values.items()]

    def set_filtered_out_values(self, column, values):
        """Set values that need to be filtered out."""
        filtered_out = [val for obj_cls_id, values in values.items() for val in values]
        self.filtered_out[column] = filtered_out
        for object_class_id, model in self.sub_models:
            model.set_filtered_out_values(column, values.get(object_class_id, {}))
        if filtered_out:
            self.setHeaderData(column, Qt.Horizontal, self.italic_font, Qt.FontRole)
        else:
            self.setHeaderData(column, Qt.Horizontal, None, Qt.FontRole)

    def clear_filtered_out_values(self):
        """Clear the set of values that need to be filtered out."""
        for column in self.filtered_out:
            self.setHeaderData(column, Qt.Horizontal, None, Qt.FontRole)
        self.filtered_out = dict()

    def rename_object_classes(self, db_map, object_classes):
        """Rename object classes in model."""
        object_class_name_column = self.header.index("object_class_name")
        object_class_id_name = {(db_map, x.id): x.name for x in object_classes}
        for object_class_id, model in self.sub_models:
            if object_class_id not in object_class_id_name:
                continue
            object_class_name = object_class_id_name[object_class_id]
            for row_data in model.sourceModel()._main_data:
                row_data[object_class_name_column] = object_class_name
        self._emit_data_changed_for_column(object_class_name_column)

    def rename_parameter_tags(self, db_map, parameter_tags):
        """Rename parameter tags in model."""
        parameter_tag_list_column = self.header.index("parameter_tag_list")
        parameter_tag_id_list_column = self.header.index("parameter_tag_id_list")
        parameter_tag_dict = {x.id: x.tag for x in parameter_tags}
        for object_class_id, model in self.sub_models:
            if object_class_id[0] != db_map:
                continue
            for row_data in model.sourceModel()._main_data:
                parameter_tag_id_list = row_data[parameter_tag_id_list_column]
                parameter_tag_list = row_data[parameter_tag_list_column]
                if not parameter_tag_id_list:
                    continue
                split_parameter_tag_id_list = [int(x) for x in parameter_tag_id_list.split(",")]
                matches = [
                    (k, tag_id) for k, tag_id in enumerate(split_parameter_tag_id_list) if tag_id in parameter_tag_dict
                ]
                if not matches:
                    continue
                split_parameter_tag_list = parameter_tag_list.split(",")
                for k, tag_id in matches:
                    new_tag = parameter_tag_dict[tag_id]
                    split_parameter_tag_list[k] = new_tag
                row_data[parameter_tag_list_column] = ",".join(split_parameter_tag_list)
        self._emit_data_changed_for_column(parameter_tag_list_column)

    def remove_object_classes(self, db_map, object_classes):
        """Remove object classes from model."""
        self.layoutAboutToBeChanged.emit()
        object_class_ids = [(db_map, x['id']) for x in object_classes]
        for i, (object_class_id, _) in reversed(list(enumerate(self.sub_models))):
            if object_class_id in object_class_ids:
                self.sub_models.pop(i)
        self.layoutChanged.emit()

    def remove_parameter_tags(self, db_map, parameter_tag_ids):
        """Remove parameter tags from model."""
        parameter_tag_list_column = self.header.index("parameter_tag_list")
        parameter_tag_id_list_column = self.header.index("parameter_tag_id_list")
        for object_class_id, model in self.sub_models:
            if object_class_id[0] != db_map:
                continue
            for row_data in model.sourceModel()._main_data:
                parameter_tag_id_list = row_data[parameter_tag_id_list_column]
                parameter_tag_list = row_data[parameter_tag_list_column]
                if not parameter_tag_id_list:
                    continue
                split_parameter_tag_id_list = [int(x) for x in parameter_tag_id_list.split(",")]
                matches = [k for k, tag_id in enumerate(split_parameter_tag_id_list) if tag_id in parameter_tag_ids]
                if not matches:
                    continue
                split_parameter_tag_list = parameter_tag_list.split(",")
                for k in sorted(matches, reverse=True):
                    del split_parameter_tag_list[k]
                row_data[parameter_tag_list_column] = ",".join(split_parameter_tag_list)
        self._emit_data_changed_for_column(parameter_tag_list_column)

    def _emit_data_changed_for_column(self, column):
        """Emits data changed for an entire column.
        Used by `rename_` and some `remove_` methods where it's too difficult to find out the exact
        rows that changed, especially because of filter status.
        """
        self.dataChanged.emit(self.index(0, column), self.index(self.rowCount() - 1, column), [Qt.DisplayRole])


class ObjectParameterValueModel(ObjectParameterModel):
    """A model that concatenates several 'sub' object parameter value models,
    one per object class.
    """

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self.empty_row_model = EmptyObjectParameterValueModel(self)
        self.empty_row_model.rowsInserted.connect(self._handle_empty_rows_inserted)
        self.object_class_name_column = None

    def reset_model(self, main_data=None):
        """Reset model data. Each sub-model is filled with parameter value data
        for a different object class."""
        self.beginResetModel()
        self.sub_models = []
        header = self.db_maps[0].object_parameter_value_fields() + ["database"]
        self.fixed_columns = [
            header.index(x) for x in ('object_class_name', 'object_name', 'parameter_name', "database")
        ]
        self.object_class_name_column = header.index('object_class_name')
        parameter_definition_id_column = header.index('parameter_id')
        object_id_column = header.index('object_id')
        db_column = header.index('database')
        self.set_horizontal_header_labels(header)
        data_dict = {}
        for db_map in self.db_maps:
            for parameter_value in db_map.object_parameter_value_list():
                object_class_id = (db_map, parameter_value.object_class_id)
                data_dict.setdefault(object_class_id, list()).append(
                    list(parameter_value) + [self._parent.db_map_to_name[db_map]]
                )
        for object_class_id, data in data_dict.items():
            source_model = SubParameterValueModel(self)
            source_model.reset_model([list(x) for x in data])
            model = ObjectParameterValueFilterProxyModel(
                self, parameter_definition_id_column, object_id_column, db_column
            )
            model.setSourceModel(source_model)
            self.sub_models.append((object_class_id, model))
        self.empty_row_model.set_horizontal_header_labels(header)
        self.empty_row_model.clear()
        self.endResetModel()

    def update_filter(self):
        """Update filter."""
        self.layoutAboutToBeChanged.emit()
        selected_parameter_definition_ids = self._parent.selected_obj_parameter_definition_ids
        selected_object_ids = self._parent.selected_object_ids
        for object_class_id, model in self.sub_models:
            parameter_definition_ids = selected_parameter_definition_ids.get(object_class_id, {})
            object_ids = selected_object_ids.get(object_class_id, {})
            model.update_filter(parameter_definition_ids, object_ids)
            model.clear_filtered_out_values()
        self.clear_filtered_out_values()
        self.layoutChanged.emit()

    def rename_objects(self, db_map, objects):
        """Rename objects in model."""
        object_id_column = self.header.index("object_id")
        object_name_column = self.header.index("object_name")
        object_dict = {}
        for object_ in objects:
            object_dict.setdefault((db_map, object_.class_id), {}).update({object_.id: object_.name})
        for object_class_id, model in self.sub_models:
            if object_class_id not in object_dict:
                continue
            object_id_name = object_dict[object_class_id]
            source_model = model.sourceModel()
            for row_data in source_model._main_data:
                object_id = row_data[object_id_column]
                if object_id in object_id_name:
                    row_data[object_name_column] = object_id_name[object_id]
        self._emit_data_changed_for_column(object_name_column)

    def rename_parameter(self, db_map, parameter):
        """Rename single parameter in model."""
        parameter_id_column = self.header.index("parameter_id")
        parameter_name_column = self.header.index("parameter_name")
        for object_class_id, model in self.sub_models:
            if object_class_id != (db_map, parameter["object_class_id"]):
                continue
            model = model.sourceModel()
            for _, row_data in enumerate(model._main_data):
                if row_data[parameter_id_column] == parameter["id"]:
                    row_data[parameter_name_column] = parameter["name"]
        self._emit_data_changed_for_column(parameter_name_column)

    def remove_objects(self, db_map, objects):
        """Remove objects from model."""
        self.layoutAboutToBeChanged.emit()
        object_id_column = self.header.index("object_id")
        object_ids = {}
        for object_ in objects:
            object_ids.setdefault((db_map, object_['class_id']), set()).add(object_['id'])
        for object_class_id, model in self.sub_models:
            if object_class_id not in object_ids:
                continue
            class_object_ids = object_ids[object_class_id]
            source_model = model.sourceModel()
            for row in reversed(range(source_model.rowCount())):
                object_id = source_model._main_data[row][object_id_column]
                if object_id in class_object_ids:
                    source_model.removeRows(row, 1)
        self.layoutChanged.emit()

    def remove_parameters(self, db_map, parameters):
        """Remove parameters from model."""
        self.layoutAboutToBeChanged.emit()
        parameter_id_column = self.header.index("parameter_id")
        parameter_ids = {}
        for parameter in parameters:
            parameter_ids.setdefault((db_map, parameter['object_class_id']), set()).add(parameter['id'])
        for object_class_id, model in self.sub_models:
            if object_class_id not in parameter_ids:
                continue
            class_parameter_ids = parameter_ids[object_class_id]
            source_model = model.sourceModel()
            for row in reversed(range(source_model.rowCount())):
                parameter_id = source_model._main_data[row][parameter_id_column]
                if parameter_id in class_parameter_ids:
                    source_model.removeRows(row, 1)
        self.layoutChanged.emit()

    def move_rows_to_sub_models(self, rows):
        """Move rows from empty row model to the a new sub_model.
        Called when the empty row model succesfully inserts new data in the db.
        """
        self.layoutAboutToBeChanged.emit()
        db_column = self.header.index('database')
        object_class_id_column = self.header.index("object_class_id")
        parameter_definition_id_column = self.header.index('parameter_id')
        object_id_column = self.header.index("object_id")
        model_data_dict = {}
        for row in rows:
            row_data = self.empty_row_model._main_data[row]
            object_class_id = row_data[object_class_id_column]
            db_map = self.db_name_to_map[row_data[db_column]]
            model_data_dict.setdefault((db_map, object_class_id), list()).append(row_data)
        for object_class_id, data in model_data_dict.items():
            source_model = SubParameterValueModel(self)
            source_model.reset_model(data)
            model = ObjectParameterValueFilterProxyModel(
                self, parameter_definition_id_column, object_id_column, db_column
            )
            model.setSourceModel(source_model)
            self.sub_models.append((object_class_id, model))
        for row in reversed(rows):
            self.empty_row_model.removeRows(row, 1)
        self.layoutChanged.emit()


class ObjectParameterDefinitionModel(ObjectParameterModel):
    """A model that concatenates several object parameter definition models
    (one per object class) vertically.
    """

    def __init__(self, parent=None):
        """Init class."""
        super().__init__(parent)
        self.empty_row_model = EmptyObjectParameterDefinitionModel(self)
        self.empty_row_model.rowsInserted.connect(self._handle_empty_rows_inserted)
        self.object_class_name_column = None

    def reset_model(self, main_data=None):
        """Reset model data. Each sub-model is filled with parameter definition data
        for a different object class."""
        self.beginResetModel()
        self.sub_models = []
        header = self.db_maps[0].object_parameter_definition_fields() + ["database"]
        self.fixed_columns = [header.index('object_class_name'), header.index('database')]
        self.object_class_name_column = header.index('object_class_name')
        parameter_definition_id_column = header.index('id')
        self.set_horizontal_header_labels(header)
        data_dict = {}
        for db_map in self.db_maps:
            for parameter_definition in db_map.object_parameter_definition_list():
                object_class_id = (db_map, parameter_definition.object_class_id)
                data_dict.setdefault(object_class_id, list()).append(
                    list(parameter_definition) + [self._parent.db_map_to_name[db_map]]
                )
        for object_class_id, data in data_dict.items():
            source_model = SubParameterDefinitionModel(self)
            source_model.reset_model([list(x) for x in data])
            model = ObjectParameterDefinitionFilterProxyModel(self, parameter_definition_id_column)
            model.setSourceModel(source_model)
            self.sub_models.append((object_class_id, model))
        self.empty_row_model.set_horizontal_header_labels(header)
        self.empty_row_model.clear()
        self.endResetModel()

    def update_filter(self):
        """Update filter."""
        self.layoutAboutToBeChanged.emit()
        selected_parameter_definition_ids = self._parent.selected_obj_parameter_definition_ids
        for object_class_id, model in self.sub_models:
            model.update_filter(selected_parameter_definition_ids.get(object_class_id, {}))
            model.clear_filtered_out_values()
        self.clear_filtered_out_values()
        self.layoutChanged.emit()

    def move_rows_to_sub_models(self, rows):
        """Move rows from empty row model to a new sub_model.
        Called when the empty row model succesfully inserts new data in the db.
        """
        self.layoutAboutToBeChanged.emit()
        db_column = self.header.index("database")
        object_class_id_column = self.header.index("object_class_id")
        parameter_definition_id_column = self.header.index('id')
        model_data_dict = {}
        for row in rows:
            row_data = self.empty_row_model._main_data[row]
            object_class_id = row_data[object_class_id_column]
            db_map = self.db_name_to_map[row_data[db_column]]
            model_data_dict.setdefault((db_map, object_class_id), list()).append(row_data)
        for object_class_id, data in model_data_dict.items():
            source_model = SubParameterDefinitionModel(self)
            source_model.reset_model(data)
            model = ObjectParameterDefinitionFilterProxyModel(self, parameter_definition_id_column)
            model.setSourceModel(source_model)
            self.sub_models.append((object_class_id, model))
        for row in reversed(rows):
            self.empty_row_model.removeRows(row, 1)
        self.layoutChanged.emit()

    def clear_parameter_value_lists(self, db_map, value_list_ids):
        """Clear parameter value_lists from model."""
        value_list_id_column = self.header.index("value_list_id")
        value_list_name_column = self.header.index("value_list_name")
        for class_id, model in self.sub_models:
            if class_id[0] != db_map:
                continue
            for row_data in model.sourceModel()._main_data:
                value_list_id = row_data[value_list_id_column]
                if value_list_id in value_list_ids:
                    row_data[value_list_id_column] = None
                    row_data[value_list_name_column] = None
        self._emit_data_changed_for_column(value_list_name_column)

    def rename_parameter_value_lists(self, db_map, value_lists):
        """Rename parameter value_lists in model."""
        value_list_id_column = self.header.index("value_list_id")
        value_list_name_column = self.header.index("value_list_name")
        parameter_value_list_dict = {x.id: x.name for x in value_lists}
        for class_id, model in self.sub_models:
            if class_id[0] != db_map:
                continue
            for row_data in model.sourceModel()._main_data:
                value_list_id = row_data[value_list_id_column]
                if value_list_id in parameter_value_list_dict:
                    row_data[value_list_name_column] = parameter_value_list_dict[value_list_id]
        self._emit_data_changed_for_column(value_list_name_column)


class ObjectParameterDefinitionFilterProxyModel(QSortFilterProxyModel):
    """A filter proxy model for object parameter models."""

    def __init__(self, parent, parameter_definition_id_column):
        """Init class."""
        super().__init__(parent)
        self.parameter_definition_ids = set()
        self.parameter_definition_id_column = parameter_definition_id_column
        self.filtered_out = dict()

    def update_filter(self, parameter_definition_ids):
        """Update filter."""
        if parameter_definition_ids == self.parameter_definition_ids:
            return
        self.parameter_definition_ids = parameter_definition_ids
        self.invalidateFilter()

    def set_filtered_out_values(self, column, values):
        """Set values that need to be filtered out."""
        if values == self.filtered_out.get(column, {}):
            return
        self.filtered_out[column] = values
        self.invalidateFilter()

    def clear_filtered_out_values(self):
        """Clear the filtered out values."""
        if not self.filtered_out:
            return
        self.filtered_out = dict()
        self.invalidateFilter()

    def auto_filter_accepts_row(self, source_row, source_parent, ignored_columns=None):
        """Accept or reject row."""
        if ignored_columns is None:
            ignored_columns = []
        for column, values in self.filtered_out.items():
            if column in ignored_columns:
                continue
            if self.sourceModel()._main_data[source_row][column] in values:
                return False
        return True

    def main_filter_accepts_row(self, source_row, source_parent):
        """Accept or reject row."""
        if self.parameter_definition_ids:
            parameter_definition_id = self.sourceModel()._main_data[source_row][self.parameter_definition_id_column]
            return parameter_definition_id in self.parameter_definition_ids
        return True

    def filterAcceptsRow(self, source_row, source_parent):
        """Accept or reject row."""
        if not self.main_filter_accepts_row(source_row, source_parent):
            return False
        if not self.auto_filter_accepts_row(source_row, source_parent):
            return False
        return True

    def batch_set_data(self, indexes, data):
        source_indexes = [self.mapToSource(x) for x in indexes]
        return self.sourceModel().batch_set_data(source_indexes, data)


class ObjectParameterValueFilterProxyModel(ObjectParameterDefinitionFilterProxyModel):
    """A filter proxy model for object parameter value models."""

    def __init__(self, parent, parameter_definition_id_column, object_id_column, db_column):
        """Init class."""
        super().__init__(parent, parameter_definition_id_column)
        self.object_ids = set()
        self.object_id_column = object_id_column
        self.db_column = db_column

    def update_filter(self, parameter_definition_ids, object_ids):  # pylint: disable=arguments-differ
        """Update filter."""
        if parameter_definition_ids == self.parameter_definition_ids and object_ids == self.object_ids:
            return
        self.parameter_definition_ids = parameter_definition_ids
        self.object_ids = object_ids
        self.invalidateFilter()

    def main_filter_accepts_row(self, source_row, source_parent):
        """Accept or reject row."""
        if not super().main_filter_accepts_row(source_row, source_parent):
            return False
        if self.object_ids:
            db = self.sourceModel()._main_data[source_row][self.db_column]
            object_id = self.sourceModel()._main_data[source_row][self.object_id_column]
            return (db, object_id) in self.object_ids
        return True
