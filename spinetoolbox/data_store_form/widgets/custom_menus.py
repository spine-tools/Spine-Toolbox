######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes for custom context menus and pop-up menus.

:author: M. Marin (KTH)
:date:   13.5.2020
"""

from PySide2.QtWidgets import QWidgetAction
from PySide2.QtCore import QEvent, QPoint, Signal, Slot
from .custom_qwidgets import LazyFilterWidget, DataToValueFilterWidget
from ...widgets.custom_menus import FilterMenuBase


class ParameterViewFilterMenu(FilterMenuBase):

    filterChanged = Signal(str, dict)

    def __init__(self, parent, source_model, field, show_empty=True):
        """
        Args:
            parent (DataStoreForm)
            source_model (CompoundParameterModel): a model to lazily get data from
            field (str): the field name
        """
        super().__init__(parent)
        self._source_model = source_model
        self._field = field
        self._filter = LazyFilterWidget(self, source_model, show_empty=show_empty)
        self._filter_action = QWidgetAction(parent)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._filter_action)
        self._menu_data = dict()  # Maps value to set of (db map, entity_class id, item id)
        self._inv_menu_data = dict()  # Maps tuple (db map, entity_class id, item id) to value
        self.connect_signals()
        self.aboutToShow.connect(self._filter.set_model)
        self._source_model.refreshed.connect(self._handle_source_model_refreshed)

    @Slot()
    def _handle_source_model_refreshed(self):
        """Updates the menu to only present values that are actually shown in the source model."""
        accepted_identifiers = {(m.db_map, m.entity_class_id, m.item_id(i)) for m, i in self._source_model._row_map}
        accepted_values = {
            value for value, identifiers in self._menu_data.items() if identifiers.intersection(accepted_identifiers)
        }
        self.set_filter_accepted_values(accepted_values)

    def set_filter_accepted_values(self, accepted_values):
        self._filter._filter_model.set_base_filter(lambda x: x in accepted_values)

    def set_filter_rejected_values(self, rejected_values):
        self._filter._filter_model.set_base_filter(lambda x: x not in rejected_values)

    def _get_value_to_remove(self, action, db_map, db_item):
        if action not in ("remove", "update"):
            return None
        entity_class_id = db_item.get(self._source_model.entity_class_id_key)
        item_id = db_item["id"]
        identifier = (db_map, entity_class_id, item_id)
        old_value = self._inv_menu_data.pop(identifier, None)
        if old_value is None:
            return None
        old_items = self._menu_data[old_value]
        old_items.remove(identifier)
        if not old_items:
            del self._menu_data[old_value]
            return old_value

    def _get_value_to_add(self, action, db_map, db_item):
        if action not in ("add", "update"):
            return None
        entity_class_id = db_item.get(self._source_model.entity_class_id_key)
        item_id = db_item["id"]
        identifier = (db_map, entity_class_id, item_id)
        value = db_map.codename if self._field == "database" else db_item[self._field]
        self._inv_menu_data[identifier] = value
        if value not in self._menu_data:
            self._menu_data[value] = {identifier}
            return value
        self._menu_data[value].add(identifier)

    def modify_menu_data(self, action, db_map, db_items):
        """Modifies data in the menu.

        Args:
            action (str): either 'add', 'remove', or 'update'
            db_map (DiffDatabaseMapping)
            db_items (list(dict))
        """
        values_to_add = list()
        values_to_remove = list()
        for db_item in db_items:
            to_remove = self._get_value_to_remove(action, db_map, db_item)
            to_add = self._get_value_to_add(action, db_map, db_item)
            if to_remove is not None:
                values_to_remove.append(to_remove)
            if to_add is not None:
                values_to_add.append(to_add)
        if values_to_remove:
            self.remove_items_from_filter_list(values_to_remove)
        if values_to_add:
            self.add_items_to_filter_list(values_to_add)

    def _build_auto_filter(self, valid_values):
        """
        Builds the auto filter given valid values.

        Args:
            valid_values (Sequence): Values accepted by the filter.

        Returns:
            dict: mapping db_map, to entity_class_id, to set of accepted parameter_value/definition ids
        """
        if not self._filter.has_filter():
            return {}  # All-pass
        if not valid_values:
            return None  # You shall not pass
        auto_filter = {}
        for value in valid_values:
            for db_map, entity_class_id, item_id in self._menu_data[value]:
                auto_filter.setdefault(db_map, {}).setdefault(entity_class_id, set()).add(item_id)
        return auto_filter

    def emit_filter_changed(self, valid_values):
        """
        Builds auto filter and emits signal.

        Args:
            valid_values (Sequence): Values accepted by the filter.
        """
        auto_filter = self._build_auto_filter(valid_values)
        self.filterChanged.emit(self._field, auto_filter)


class TabularViewFilterMenu(FilterMenuBase):
    """Filter menu to use together with FilterWidget in TabularViewMixin."""

    filterChanged = Signal(str, set, bool)

    def __init__(self, parent, identifier, data_to_value, show_empty=True):
        """
        Args:
            parent (DataStoreForm)
            identifier (int): index identifier
            data_to_value (method): a method to translate item data to a value for display role
        """
        super().__init__(parent)
        self.identifier = identifier
        self._filter = DataToValueFilterWidget(self, data_to_value, show_empty=show_empty)
        self._filter_action = QWidgetAction(parent)
        self._filter_action.setDefaultWidget(self._filter)
        self.addAction(self._filter_action)
        self.anchor = parent
        self.connect_signals()

    def emit_filter_changed(self, valid_values):
        self.filterChanged.emit(self.identifier, valid_values, self._filter.has_filter())

    def event(self, event):
        if event.type() == QEvent.Show and self.anchor is not None:
            if self.anchor.area == "rows":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(0, self.anchor.height())
            elif self.anchor.area == "columns":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(self.anchor.width(), 0)
            self.move(pos)
        return super().event(event)
