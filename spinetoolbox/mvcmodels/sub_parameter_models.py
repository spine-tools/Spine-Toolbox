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
from ..helpers import busy_effect
from .minimal_table_model import MinimalTableModel
from .parameter_value_formatting import format_for_DisplayRole, format_for_ToolTipRole


class SubParameterModel(MinimalTableModel):
    """A parameter model which corresponds to a slice of the entire table.
    The idea is to combine several of these into one big model.
    Allows specifying set of columns that are non-editable (e.g., object_class_name)
    TODO: how column insertion/removal impacts fixed_columns?
    """

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        self.gray_brush = QGuiApplication.palette().button()
        self.error_log = []
        self.updated_count = 0

    def flags(self, index):
        """Make fixed indexes non-editable."""
        flags = super().flags(index)
        if index.column() in self._parent.fixed_columns:
            return flags & ~Qt.ItemIsEditable
        return flags

    def data(self, index, role=Qt.DisplayRole):
        """Paint background of fixed indexes gray."""
        if role != Qt.BackgroundRole:
            return super().data(index, role)
        if index.column() in self._parent.fixed_columns:
            return self.gray_brush
        return super().data(index, role)

    def batch_set_data(self, indexes, data):
        """Batch set data for indexes.
        Try and update data in the database first, and if successful set data in the model.
        """
        self.error_log = []
        self.updated_count = 0
        if not indexes:
            return False
        if len(indexes) != len(data):
            return False
        items_to_update = self.items_to_update(indexes, data)
        upd_ids = self.update_items_in_db(items_to_update)
        header = self._parent.horizontal_header_labels()
        id_column = header.index('id')
        db_column = header.index('database')
        for k, index in enumerate(indexes):
            db_name = self._main_data[index.row()][db_column]
            db_map = self._parent.db_name_to_map[db_name]
            id_ = self._main_data[index.row()][id_column]
            if (db_map, id_) not in upd_ids:
                continue
            self._main_data[index.row()][index.column()] = data[k]
        return True

    def items_to_update(self, indexes, data):
        """A list of items (dict) to update in the database."""
        raise NotImplementedError()

    def update_items_in_db(self, items_to_update):
        """A list of ids of items updated in the database."""
        raise NotImplementedError()


class SubParameterValueModel(SubParameterModel):
    """A parameter model which corresponds to a slice of an entire parameter value table.
    The idea is to combine several of these into one big model.
    """

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent

    def items_to_update(self, indexes, data):
        """A list of items (dict) for updating in the database."""
        items_to_update = dict()
        header = self._parent.horizontal_header_labels()
        db_column = header.index('database')
        id_column = header.index('id')
        for k, index in enumerate(indexes):
            row = index.row()
            db_name = index.sibling(row, db_column).data(Qt.EditRole)
            db_map = self._parent.db_name_to_map[db_name]
            id_ = index.sibling(row, id_column).data(Qt.EditRole)
            if not id_:
                continue
            field_name = header[index.column()]
            if field_name != "value":
                continue
            value = data[k]
            if value == index.data(Qt.EditRole):
                # nothing to do really
                continue
            item = {"id": id_, "value": value}
            items_to_update.setdefault(db_map, {}).setdefault(id_, {}).update(item)
        return {db_map: list(item_d.values()) for db_map, item_d in items_to_update.items()}

    @busy_effect
    def update_items_in_db(self, items_to_update):
        """Try and update parameter values in database."""
        upd_ids = []
        for db_map, items in items_to_update.items():
            upd_items, error_log = db_map.update_parameter_values(*items)
            self.updated_count += upd_items.count()
            self.error_log += error_log
            upd_ids += [(db_map, x.id) for x in upd_items]
        return upd_ids

    def data(self, index, role=Qt.DisplayRole):
        """Limit the display of JSON data."""
        if self._parent.header[index.column()] == 'value':
            if role == Qt.ToolTipRole:
                return format_for_ToolTipRole(super().data(index, Qt.EditRole))
            if role == Qt.DisplayRole:
                return format_for_DisplayRole(super().data(index, Qt.EditRole))
        return super().data(index, role)


class SubParameterDefinitionModel(SubParameterModel):
    """A parameter model which corresponds to a slice of an entire parameter definition table.
    The idea is to combine several of these into one big model.
    """

    def __init__(self, parent):
        """Initialize class."""
        super().__init__(parent)
        self._parent = parent

    def items_to_update(self, indexes, data):
        """A list of items (dict) for updating in the database."""
        items_to_update = dict()
        header = self._parent.horizontal_header_labels()
        db_column = header.index('database')
        id_column = header.index('id')
        parameter_tag_id_list_column = header.index('parameter_tag_id_list')
        value_list_id_column = header.index('value_list_id')
        parameter_tag_dict = {}
        parameter_value_list_dict = {}
        new_indexes = []
        new_data = []
        for index, value in zip(indexes, data):
            row = index.row()
            db_name = index.sibling(row, db_column).data(Qt.EditRole)
            db_map = self._parent.db_name_to_map[db_name]
            id_ = index.sibling(row, id_column).data(Qt.EditRole)
            if not id_:
                continue
            field_name = header[index.column()]
            item = {"id": id_}
            # Handle changes in parameter tag list: update tag id list accordingly
            if field_name == "parameter_tag_list":
                split_parameter_tag_list = value.split(",") if value else []
                d = parameter_tag_dict.setdefault(db_map, {x.tag: x.id for x in db_map.parameter_tag_list()})
                try:
                    parameter_tag_id_list = ",".join(str(d[x]) for x in split_parameter_tag_list)
                    new_indexes.append(index.sibling(row, parameter_tag_id_list_column))
                    new_data.append(parameter_tag_id_list)
                    item.update({'parameter_tag_id_list': parameter_tag_id_list})
                except KeyError as e:
                    self.error_log.append("Invalid parameter tag '{}'.".format(e))
            # Handle changes in value_list name: update value_list id accordingly
            elif field_name == "value_list_name":
                value_list_name = value
                d = parameter_value_list_dict.setdefault(
                    db_map, {x.name: x.id for x in db_map.wide_parameter_value_list_list()}
                )
                try:
                    value_list_id = d[value_list_name]
                    new_indexes.append(index.sibling(row, value_list_id_column))
                    new_data.append(value_list_id)
                    item.update({'parameter_value_list_id': value_list_id})
                except KeyError:
                    self.error_log.append("Invalid value list '{}'.".format(value_list_name))
            elif field_name == "parameter_name":
                item.update({"name": value})
            elif field_name == "default_value":
                default_value = value
                if default_value != index.data(Qt.EditRole):
                    item.update({"default_value": default_value})
            items_to_update.setdefault(db_map, {}).setdefault(id_, {}).update(item)
        indexes.extend(new_indexes)
        data.extend(new_data)
        return {db_map: list(item_d.values()) for db_map, item_d in items_to_update.items()}

    @busy_effect
    def update_items_in_db(self, items_to_update):
        """Try and update parameter definitions in database."""
        upd_ids = []
        for db_map, items in items_to_update.items():
            tag_dict = dict()
            for item in items:
                parameter_tag_id_list = item.pop("parameter_tag_id_list", None)
                if parameter_tag_id_list is None:
                    continue
                tag_dict[item["id"]] = parameter_tag_id_list
            upd_def_tag_list, def_tag_error_log = db_map.set_parameter_definition_tags(tag_dict)
            upd_params, param_error_log = db_map.update_parameter_definitions(*items)
            self.updated_count += len(upd_def_tag_list) + upd_params.count()
            self.error_log += def_tag_error_log + param_error_log
            upd_ids += [(db_map, x.parameter_definition_id) for x in upd_def_tag_list]
            upd_ids += [(db_map, x.id) for x in upd_params]
        return upd_ids

    def data(self, index, role=Qt.DisplayRole):
        """Limit the display of JSON data."""
        if self._parent.header[index.column()] == 'default_value':
            if role == Qt.ToolTipRole:
                return format_for_ToolTipRole(super().data(index, Qt.EditRole))
            if role == Qt.DisplayRole:
                return format_for_DisplayRole(super().data(index, Qt.EditRole))
        return super().data(index, role)
