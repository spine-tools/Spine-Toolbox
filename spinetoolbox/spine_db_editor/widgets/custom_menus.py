######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
"""

from PySide6.QtWidgets import QMenu, QWidget
from PySide6.QtCore import Qt, QEvent, QPoint, Signal
from PySide6.QtGui import QKeyEvent, QKeySequence
from ...widgets.custom_menus import FilterMenuBase
from ...mvcmodels.filter_checkbox_list_model import LazyFilterCheckboxListModel
from ...fetch_parent import FlexibleFetchParent
from ...helpers import DB_ITEM_SEPARATOR


class MainMenu(QMenu):
    def event(self, ev):
        """Intercepts shortcuts and instead sends an equivalent event with the 'Alt' modifier,
        so that mnemonics works with just the key.
        Also sends a key press event with the 'Alt' key when this menu shows,
        so that mnemonics are underlined on Windows.
        """
        if ev.type() == QEvent.KeyPress and ev.key() == Qt.Key_Alt:
            return True
        if ev.type() == QEvent.ShortcutOverride and ev.modifiers() == Qt.NoModifier:
            actions = self.actions() + [a for child in self.findChildren(QWidget) for a in child.actions()]
            mnemonics = [QKeySequence.mnemonic(a.text()) for a in actions]
            key_seq = QKeySequence(Qt.ALT | Qt.Key(ev.key()))
            if key_seq in mnemonics:
                ev = QKeyEvent(QEvent.KeyPress, ev.key(), Qt.AltModifier)
                qApp.postEvent(self, ev)  # pylint: disable=undefined-variable
                return True
        if ev.type() == QEvent.Show:
            pev = QKeyEvent(QEvent.KeyPress, Qt.Key_Alt, Qt.NoModifier)
            qApp.postEvent(self, pev)  # pylint: disable=undefined-variable
        return super().event(ev)


class ParameterViewFilterMenu(FilterMenuBase):
    filterChanged = Signal(str, object)

    def __init__(self, parent, db_mngr, db_maps, item_type, entity_class_id_key, field, show_empty=True):
        """
        Args:
            parent (SpineDBEditor)
            db_mngr (SpineDBManager)
            db_maps (Sequence of DatabaseMapping)
            item_type (str)
            entity_class_id_key (str)
            field (str): the field name
        """
        super().__init__(parent)
        self._item_type = item_type
        self._db_mngr = db_mngr
        self._entity_class_id_key = entity_class_id_key
        self._field = field
        self._menu_data = dict()  # Maps display value to set of (db map, entity_class_id, actual value) tuples
        fetch_parent = FlexibleFetchParent(
            self._item_type,
            handle_items_added=self._handle_items_added,
            handle_items_removed=self._handle_items_removed,
            accepts_item=self._accepts_item,
            owner=self,
            chunk_size=None,
        )
        self._set_up(LazyFilterCheckboxListModel, self, db_mngr, db_maps, fetch_parent, show_empty=show_empty)

    def set_filter_accepted_values(self, accepted_values):
        if self._filter._filter_model.canFetchMore(None):
            self._filter._filter_model.fetchMore(None)
        self._filter._filter_model.filter_by_condition(lambda x: x in accepted_values)
        self._filter._apply_filter()

    def set_filter_rejected_values(self, rejected_values):
        if self._filter._filter_model.canFetchMore(None):
            self._filter._filter_model.fetchMore(None)
        self._filter._filter_model.filter_by_condition(lambda x: x not in rejected_values)
        self._filter._apply_filter()

    def _get_value(self, item, db_map):
        if self._field == "database":
            return db_map.codename
        return item[self._field]

    def _get_display_value(self, item, db_map):
        if self._field in ("value", "default_value"):
            return self._db_mngr.get_value(db_map, self._item_type, item["id"], role=Qt.DisplayRole)
        if self._field in ("object_class_name_list", "object_name_list"):
            return DB_ITEM_SEPARATOR.join(item[self._field])
        return self._get_value(item, db_map) or "(empty)"

    def _accepts_item(self, item, db_map):
        return item.get(self._entity_class_id_key) is not None

    def _handle_items_added(self, db_map_data):
        to_add = set()
        for db_map, items in db_map_data.items():
            for item in items:
                display_value = self._get_display_value(item, db_map)
                value = self._get_value(item, db_map)
                to_add.add(display_value)
                self._menu_data.setdefault(display_value, set()).add((db_map, item["entity_class_id"], value))
        self.add_items_to_filter_list(to_add)

    def _handle_items_removed(self, db_map_data):
        for db_map, items in db_map_data.items():
            for item in items:
                display_value = self._get_display_value(item, db_map)
                value = self._get_value(item, db_map)
                self._menu_data.get(display_value, set()).discard((db_map, item["entity_class_id"], value))
        to_remove = {display_value for display_value, data in self._menu_data.items() if not data}
        for display_value in to_remove:
            del self._menu_data[display_value]
        self.remove_items_from_filter_list(to_remove)

    def _build_auto_filter(self, valid_values):
        """
        Builds the auto filter given valid values.

        Args:
            valid_values (Sequence): Values accepted by the filter.

        Returns:
            dict: mapping (db_map, entity_class_id) to set of valid values
        """
        if not self._filter.has_filter():
            return {}  # All-pass
        if not valid_values:
            return None  # You shall not pass
        auto_filter = {}
        for display_value in valid_values:
            for db_map, entity_class_id, value in self._menu_data[display_value]:
                auto_filter.setdefault((db_map, entity_class_id), set()).add(value)
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

    def __init__(self, parent, db_mngr, db_maps, item_type, accepts_item, identifier, show_empty=True):
        """
        Args:
            parent (SpineDBEditor)
            db_mngr (SpineDBManager)
            db_maps (Sequence of DatabaseMapping)
            item_type (str)
            accepts_item (function)
            identifier (int): index identifier
        """
        super().__init__(parent)
        self.anchor = parent
        self._db_mngr = db_mngr
        self._item_type = item_type
        self._identifier = identifier
        self._menu_data = {}
        fetch_parent = FlexibleFetchParent(
            self._item_type,
            handle_items_added=self._handle_items_added,
            handle_items_removed=self._handle_items_removed,
            accepts_item=accepts_item,
            owner=self,
            chunk_size=None,
        )
        self._set_up(LazyFilterCheckboxListModel, self, db_mngr, db_maps, fetch_parent, show_empty=show_empty)

    def _handle_items_added(self, db_map_data):
        to_add = set()
        for db_map, items in db_map_data.items():
            for item in items:
                for display_value, value in self._get_values(db_map, item):
                    to_add.add(display_value)
                    self._menu_data.setdefault(display_value, set()).add(value)
        self.add_items_to_filter_list(to_add)

    def _get_values(self, db_map, item):
        if self._item_type == "parameter_value":
            for index in self._db_mngr.get_value_indexes(db_map, "parameter_value", item["id"]):
                yield str(index), (None, index)
        else:
            yield item["name"], (db_map, item["id"])

    def _handle_items_removed(self, db_map_data):
        for db_map, items in db_map_data.items():
            for item in items:
                display_value = item["name"]
                self._menu_data.get(display_value, set()).discard((db_map, item["id"]))
        to_remove = {display_value for display_value, data in self._menu_data.items() if not data}
        for display_value in to_remove:
            del self._menu_data[display_value]
        self.remove_items_from_filter_list(to_remove)

    def emit_filter_changed(self, valid_values):
        valid_values = {db_map_id for v in valid_values for db_map_id in self._menu_data[v]}
        self.filterChanged.emit(self._identifier, valid_values, self._filter.has_filter())

    def event(self, event):
        if event.type() == QEvent.Show and self.anchor is not None:
            if self.anchor.area == "rows":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(0, self.anchor.height())
            elif self.anchor.area == "columns":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(self.anchor.width(), 0)
            self.move(pos)
        return super().event(event)
